import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class WSLConfig:
    host: str = os.getenv("WSL_HOST", "127.0.0.1")
    user: str = os.getenv("WSL_USER", "kali")
    password: str = os.getenv("WSL_PASS", "kali")
    port: int = int(os.getenv("WSL_PORT", 22))
    distro: str = os.getenv("WSL_DISTRO", "kali-linux")


class WSLBridge:
    """Responsible only for WSL/SSH service configuration and readiness."""

    def __init__(self, config: WSLConfig | None = None):
        self.config = config or WSLConfig()
        self._lock = threading.Lock()

    def ensure_ssh_service(self) -> bool:
        """Start SSH service inside WSL when local SSH port is closed."""
        with self._lock:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    if sock.connect_ex((self.config.host, self.config.port)) == 0:
                        return True

                print(f"[*] Starting SSH service on {self.config.distro}...")
                start_cmd = (
                    f"wsl -d {self.config.distro} -u root bash -c "
                    '"mkdir -p /run/sshd && /usr/sbin/sshd"'
                )
                subprocess.run(start_cmd, shell=True, capture_output=True, timeout=10)
                time.sleep(1)
                return True
            except Exception:
                return False
