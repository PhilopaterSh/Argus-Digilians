import socket
import subprocess
import time
import paramiko
from app.core.config import ArgusConfig
from app.tools.utils import clean_ansi_codes
from app.tools.wsl_bridge import WSLBridge

# config.yaml is the single source of truth for this default (2026-07-10
# audit): `command_timeout_seconds` was defined in ArgusConfig but nothing
# in the codebase actually read it - confirmed via grep, every real
# `.run(..., timeout=N)` call site hardcodes its own tool-specific value
# (nmap gets 180s, DNS gets 20s, etc. - deliberately NOT overridden here,
# those per-tool values are already well-tuned), so this constant was only
# ever reached when a caller passed no `timeout=` at all. Wired to
# config.yaml so that fallback path is actually controlled by it, instead
# of being a second, silently-independent "default timeout" setting.
try:
    DEFAULT_COMMAND_TIMEOUT = ArgusConfig.load().command_timeout_seconds
except Exception:
    DEFAULT_COMMAND_TIMEOUT = 180

class CommandRunner:
    """Responsible only for executing commands through WSL or SSH fallback."""

    def __init__(self, bridge: WSLBridge):
        self.bridge = bridge

    @property
    def config(self):
        return self.bridge.config

    def _is_waf_blocked(self, text):
        """Detects if the target has restricted access based on common block pages."""
        indicators = [
            "Access Temporarily Restricted",
            "possibly malicious",
            "automated security systems",
            "Cloudflare ray ID",
            "IP address as possibly malicious"
        ]
        for ind in indicators:
            if ind.lower() in text.lower():
                return True
        return False

    def run(self, command: str, show_prompt: bool = False, timeout: int = DEFAULT_COMMAND_TIMEOUT) -> str:
        """Execute a command in WSL Kali with guided error reporting.

        `timeout` bounds a single command so one slow/unresponsive tool call
        can't silently consume the entire outer agent-run budget (see
        scripts/run_agent.py's AGENT_TIMEOUT_SECONDS).
        """
        if self.config.host in ["127.0.0.1", "localhost"]:
            return self._run_direct_wsl(command, show_prompt, timeout=timeout)
        return self._run_ssh(command, timeout=timeout)

    def _run_direct_wsl(self, command: str, show_prompt: bool = False, timeout: int = DEFAULT_COMMAND_TIMEOUT) -> str:
        try:
            wsl_cmd = [
                "wsl",
                "-d",
                self.config.distro,
                "-u",
                self.config.user,
                "bash",
                "-c",
                command,
            ]
            result = subprocess.run(
                wsl_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="ignore",
                # Explicit stdin avoids inheriting the parent process's stdin
                # handle. Normally harmless, but in a non-standard launch
                # context (e.g. a test harness or headless spawn with no real
                # console attached) an inherited/invalid stdin handle can
                # make CreateProcess fail outright with
                # OSError: [Errno 22] Invalid argument before the command
                # ever runs - observed once via Streamlit's AppTest harness,
                # not through the real dashboard.
                stdin=subprocess.DEVNULL,
            )

            output = result.stdout if result.stdout else result.stderr
            cleaned = clean_ansi_codes(output)

            # WAF Detection
            if self._is_waf_blocked(cleaned):
                return f"[STOP] [WAF ALERT] Access Restricted! The target has blocked your IP. Suggestion: STOP SCANS IMMEDIATELY and wait 15-30 mins or use a VPN/Proxy."

            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                lower_error = error_msg.lower()
                if "command not found" in lower_error:
                    return f"Error: Tool not installed in WSL. Suggestion: Use 'Run_Kali_Command' with 'sudo apt install -y {command.split()[0]}' to add the missing tool."
                if "flag provided but not defined" in lower_error or "invalid option" in lower_error:
                    return f"Error: Syntax Error in command. Suggestion: Use 'Run_Kali_Command' with '{command.split()[0]} --help' to verify the correct parameters."
                if "permission denied" in lower_error:
                    return "Error: Permission denied. Suggestion: Try running with 'sudo' or check file permissions."
                return f"Error (Code {result.returncode}): {cleaned}"

            if show_prompt:
                return f"+--(kali@WSL)-[~]\n+-$ {command}\n{cleaned}"
            return cleaned
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout}s. Suggestion: The target might be slow or blocking the scan. Try narrowing the scope or increasing the timeout."
        except Exception as exc:
            return f"Bridge Error: {exc}"

    def _run_ssh(self, command: str, timeout: int = DEFAULT_COMMAND_TIMEOUT) -> str:
        max_retries = 2
        for attempt in range(max_retries):
            self.bridge.ensure_ssh_service()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    self.config.host,
                    port=self.config.port,
                    username=self.config.user,
                    password=self.config.password,
                    timeout=15,
                )
                # exec_command()'s own timeout only bounds the exec request itself;
                # without settimeout() on the channel, stdout.read()/stderr.read()
                # below block forever on a hung/slow remote command.
                _, stdout, stderr = client.exec_command(command, timeout=timeout)
                stdout.channel.settimeout(timeout)
                try:
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                except socket.timeout:
                    client.close()
                    return f"Error: SSH command timed out after {timeout}s. Suggestion: The target might be slow or blocking the scan. Try narrowing the scope or increasing the timeout."
                client.close()

                cleaned_out = clean_ansi_codes(output if output else error)
                if self._is_waf_blocked(cleaned_out):
                     return f"[STOP] [WAF ALERT] Access Restricted via SSH! Target blocked IP."

                if error and not output:
                    return f"SSH Command Error: {error}"
                return cleaned_out
            except Exception as exc:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return f"SSH Bridge Error: {exc}"
        return "Bridge Error: Command execution failed."
