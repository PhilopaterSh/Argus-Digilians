import subprocess
import time

import paramiko

from tools.utils import clean_ansi_codes
from tools.wsl_bridge import WSLBridge


class CommandRunner:
    """Responsible only for executing commands through WSL or SSH fallback."""

    def __init__(self, bridge: WSLBridge):
        self.bridge = bridge

    @property
    def config(self):
        return self.bridge.config

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

            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                lower_error = error_msg.lower()
                if "command not found" in lower_error:
                    return "Error: Tool not installed in WSL. Suggestion: Use 'apt install' to add the missing tool."
                if "permission denied" in lower_error:
                    return "Error: Permission denied. Suggestion: Try running with 'sudo' or check file permissions."
                return f"Error (Code {result.returncode}): {clean_ansi_codes(error_msg)}"

            final_output = result.stdout if result.stdout else result.stderr
            cleaned = clean_ansi_codes(final_output)

            if show_prompt:
                return f"┌──(kali㉿WSL)-[~]\n└─$ {command}\n{cleaned}"
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

                if error and not output:
                    return f"SSH Command Error: {error}"
                return clean_ansi_codes(output if output else error)
            except Exception as exc:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return f"SSH Bridge Error: {exc}"

        return "Bridge Error: Command execution failed."
