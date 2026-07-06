import subprocess
import time
import paramiko
from app.tools.utils import clean_ansi_codes
from app.tools.wsl_bridge import WSLBridge

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

    def run(self, command: str, show_prompt: bool = False) -> str:
        """Execute a command in WSL Kali with guided error reporting."""
        if self.config.host in ["127.0.0.1", "localhost"]:
            return self._run_direct_wsl(command, show_prompt)
        return self._run_ssh(command)

    def _run_direct_wsl(self, command: str, show_prompt: bool = False) -> str:
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
                timeout=600,
                encoding="utf-8",
                errors="ignore",
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
            return "Error: Command timed out after 600s. Suggestion: The target might be slow or blocking the scan. Try narrowing the scope or increasing the timeout."
        except Exception as exc:
            return f"Bridge Error: {exc}"

    def _run_ssh(self, command: str) -> str:
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
                _, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
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
