# Research: Self-Healing Expansion

**Phase**: 0 — Technical Research | **Date**: 2026-06-29

---

## Current State

`SelfHealingService` in `app/tools/self_heal.py` (31 lines):

```python
class SelfHealingService:
    def __init__(self, runner):
        self.runner = runner
    
    def system_self_heal(self, tool_info):
        # Only handles:
        # 1. "pip install <pkg>" → subprocess.run pip install
        # 2. Anything else → sudo apt-get install via runner
        ...
```

### Lackings

- No `health_check()` method
- No `restart_service()` method
- No proactive monitoring (watchdog)
- No config repair
- No error recovery beyond "install missing tool"
- Not registered as LangChain Tool in GUI (but IS in WSLBridgeTools)

### Design for New Methods

```python
class SelfHealingService:
    def __init__(self, runner):
        self.runner = runner
    
    def system_self_heal(self, tool_info) -> str:
        """Existing method — unchanged."""
    
    def health_check(self) -> dict:
        """Check WSL, Ollama, Python venv."""
        return {
            "wsl": self._check_wsl(),
            "ollama": self._check_ollama(),
            "python": self._check_python(),
        }
    
    def restart_service(self, name: str) -> str:
        """Restart a named service."""
        if name == "ollama":
            return self._restart_ollama()
        elif name == "wsl":
            return self._restart_wsl()
        else:
            return f"Unknown service: {name}"
    
    def _check_wsl(self) -> str:
        """Run 'wsl --status' or ping Kali."""
    
    def _check_ollama(self) -> str:
        """HTTP GET localhost:11434/api/tags."""
    
    def _check_python(self) -> str:
        """Verify python --version and key imports."""
    
    def _restart_ollama(self) -> str:
        """Kill ollama.exe and restart via Windows."""
    
    def _restart_wsl(self) -> str:
        """wsl --terminate kali-linux then re-init bridge."""
```
