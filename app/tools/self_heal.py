import os
import sys
import subprocess
import urllib.request
import json
import logging
from typing import Any

from app.core.registry.base_tool import BaseToolService, ToolMetadata

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/tags"
OLLAMA_HEALTH_TIMEOUT = 5
WSL_TERMINATE_TIMEOUT = 10
# subprocess.CREATE_NO_WINDOW only exists on Windows; accessing it directly raises
# AttributeError on Linux/macOS before Popen is even called (this module's real target
# is Windows, per the project's Technical Context, but it must still be importable and
# testable on a Linux CI runner). 0 is a no-op creationflags value everywhere else.
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class SelfHealingService(BaseToolService):
    """Attempts to autonomously install missing libraries or tools."""

    def __init__(self, runner):
        """Store the command runner used for Kali/system-tool installs."""
        self.runner = runner

    @property
    def metadata(self) -> ToolMetadata:
        """Metadata."""
        return ToolMetadata(
            name="self_heal",
            description="Autonomously install missing Python libraries or Kali system tools",
            version="2.0.0",
        )

    def execute(self, **kwargs) -> str:
        """BaseToolService entry point: extract `tool_info` and self-heal.

        Args:
            **kwargs: Must include `tool_info` (str); missing it defaults
                to an empty string.

        Returns:
            str: The result of `system_self_heal(tool_info)`.
        """
        tool_info = kwargs.get("tool_info", "")
        return self.system_self_heal(tool_info)

    def system_self_heal(self, tool_info: str) -> str:
        """Attempts to autonomously install missing libraries or tools (Self-Healing).

        Args:
            tool_info (str): Either a pip-install-style hint (containing
                "pip install" or "import") naming a Python package, or a
                Kali/system tool name to install via `apt-get`.

        Returns:
            str: A human-readable success/failure message.
        """
        print(f"[*] [Argus-SelfHeal] AI requested repair for: {tool_info}")
        
        # 1. Check if it's a Python library
        if "pip install" in tool_info.lower() or "import" in tool_info.lower():
            package = tool_info.split("install")[-1].strip().split()[0] if "install" in tool_info else tool_info.split()[-1]
            print(f"[*] Attempting to install Python package: {package}")
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", package],
                capture_output=True, text=True,
            )
            if res.returncode == 0:
                return f"Successfully installed Python package: {package}. You can now retry the failed action."
            else:
                return f"Failed to install {package}: {res.stderr}"

        # 2. Check if it's a Kali/System tool
        print(f"[*] Attempting to install Kali tool via apt: {tool_info}")
        res = self.runner.run(f"sudo apt-get update && sudo apt-get install -y {tool_info}")
        if "Setting up" in res or "is already the newest version" in res:
            return f"Successfully installed/verified system tool: {tool_info}."
        
        return f"Self-heal failed for {tool_info}. Please check logs or install manually."

    def health_check(self) -> dict:
        """Health check."""
        return {
            "wsl": self._check_wsl(),
            "ollama": self._check_ollama(),
            "python": self._check_python(),
        }

    def _check_wsl(self) -> str:
        """Check wsl."""
        try:
            # wsl.exe writes UTF-16LE to stdout/stderr; text=True decodes with the
            # default locale, which turns it into a null-byte-interleaved mess
            # (harmless for the returncode check below, but unreadable in the
            # failure diagnostic). Capture raw bytes and decode explicitly instead.
            res = subprocess.run(
                ["wsl", "--status"],
                capture_output=True, timeout=10,
            )
            if res.returncode == 0:
                return "ok"
            stderr = res.stderr.decode("utf-16-le", errors="ignore").strip()
            stdout = res.stdout.decode("utf-16-le", errors="ignore").strip()
            return f"failed: {stderr or stdout}"
        except subprocess.TimeoutExpired:
            return "failed: timeout"
        except FileNotFoundError:
            return "failed: wsl.exe not found"
        except Exception as e:
            return f"failed: {e}"

    def _check_ollama(self) -> str:
        """Check ollama."""
        try:
            req = urllib.request.Request(OLLAMA_URL)
            with urllib.request.urlopen(req, timeout=OLLAMA_HEALTH_TIMEOUT) as resp:
                if resp.status == 200:
                    return "ok"
                return f"failed: HTTP {resp.status}"
        except urllib.error.URLError as e:
            return f"failed: cannot reach Ollama ({e.reason})"
        except Exception as e:
            return f"failed: {e}"

    def _check_python(self) -> str:
        """Check python."""
        try:
            ver = sys.version.split()[0]
            venv = sys.prefix
            return f"ok (Python {ver}, venv: {os.path.basename(venv)})"
        except Exception as e:
            return f"failed: {e}"

    def restart_service(self, name: str) -> str:
        """Restart a named managed service.

        Args:
            name (str): Service name - "ollama" or "wsl" (case-insensitive).

        Returns:
            str: A human-readable success/failure message, or
            "Unknown service: <name>" for any other name.
        """
        name = name.lower().strip()
        if name == "ollama":
            return self._restart_ollama()
        elif name == "wsl":
            return self._restart_wsl()
        else:
            return f"Unknown service: {name}"

    def _restart_ollama(self) -> str:
        """Kill any running `ollama.exe` and relaunch it via `ollama serve`.

        Returns:
            str: A human-readable success/failure message (including when
            `ollama.exe` isn't on PATH).
        """
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "ollama.exe"],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=CREATE_NO_WINDOW,
            )
            return "Successfully restarted Ollama."
        except FileNotFoundError:
            return "Failed: ollama.exe not found in PATH."
        except Exception as e:
            return f"Failed to restart Ollama: {e}"

    def _restart_wsl(self) -> str:
        """Restart wsl."""
        try:
            subprocess.run(
                ["wsl", "--terminate", "kali-linux"],
                capture_output=True, text=True, timeout=WSL_TERMINATE_TIMEOUT,
            )
            res = subprocess.run(
                ["wsl", "-d", "kali-linux", "echo", "ready"],
                capture_output=True, text=True, timeout=30,
            )
            if res.returncode == 0:
                return "Successfully restarted WSL (kali-linux)."
            return f"WSL restart completed but verification failed: {res.stderr}"
        except subprocess.TimeoutExpired:
            return "Failed: WSL restart timed out."
        except FileNotFoundError:
            return "Failed: wsl.exe not found."
        except Exception as e:
            return f"Failed to restart WSL: {e}"
