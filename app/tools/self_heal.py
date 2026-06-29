import sys
import subprocess
from typing import Any

from app.core.registry.base_tool import BaseToolService, ToolMetadata


class SelfHealingService(BaseToolService):
    """Attempts to autonomously install missing libraries or tools."""

    def __init__(self, runner):
        self.runner = runner

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="self_heal",
            description="Autonomously install missing Python libraries or Kali system tools",
            version="2.0.0",
        )

    def execute(self, **kwargs) -> str:
        tool_info = kwargs.get("tool_info", "")
        return self.system_self_heal(tool_info)

    def system_self_heal(self, tool_info: str) -> str:
        """Attempts to autonomously install missing libraries or tools (Self-Healing)."""
        print(f"[*] [Argus-SelfHeal] AI requested repair for: {tool_info}")
        
        # 1. Check if it's a Python library
        if "pip install" in tool_info.lower() or "import" in tool_info.lower():
            package = tool_info.split("install")[-1].strip().split()[0] if "install" in tool_info else tool_info.split()[-1]
            print(f"[*] Attempting to install Python package: {package}")
            cmd = f"{sys.executable} -m pip install -U {package}"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
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
