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
    host: str     = os.getenv("WSL_HOST",   "127.0.0.1")
    user: str     = os.getenv("WSL_USER",   "kali")
    # ⚠️ Never hardcode passwords. Set WSL_PASS in your .env file.
    password: str = os.getenv("WSL_PASS",   "")
    port: int     = int(os.getenv("WSL_PORT", 22))
    distro: str   = os.getenv("WSL_DISTRO", "kali-linux")

    def __post_init__(self):
        # Warn if password not set
        if not self.password:
            import warnings
            warnings.warn(
                "WSL_PASS is not set. SSH fallback will fail. Set it in your .env file.",
                UserWarning, stacklevel=2
            )

        # Normalize/validate distro: if the configured distro name is not present,
        # attempt a fuzzy match against installed WSL distributions and pick a sensible default.
        try:
            res = subprocess.run(["wsl", "-l", "-q"], capture_output=True, text=True, timeout=3)
            installed = [d.strip() for d in res.stdout.splitlines() if d.strip()]
            if installed:
                # Exact match OK
                if self.distro not in installed:
                    # Try partial match (startswith or contains)
                    lower = self.distro.lower()
                    match = None
                    for d in installed:
                        if d.lower() == lower or d.lower().startswith(lower) or lower in d.lower():
                            match = d
                            break
                    if match:
                        self.distro = match
                    else:
                        # Prefer any running distro, otherwise pick first installed
                        try:
                            res2 = subprocess.run(["wsl", "-l", "-v"], capture_output=True, text=True, timeout=3)
                            lines = [l for l in res2.stdout.splitlines() if l.strip()]
                            running = None
                            for l in lines:
                                if "Running" in l:
                                    parts = l.split()
                                    # name is first non-empty token
                                    for p in parts:
                                        if p and p != "NAME" and p != "STATE" and p != "VERSION":
                                            running = p
                                            break
                                    if running:
                                        break
                            if running and running in installed:
                                self.distro = running
                            else:
                                self.distro = installed[0]
                        except Exception:
                            self.distro = installed[0]
        except Exception:
            # If wsl command is unavailable or fails, keep provided distro
            pass

class WSLBridge:
    """Responsible only for WSL/SSH service configuration and readiness."""
    def __init__(self, config: WSLConfig = None):
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
