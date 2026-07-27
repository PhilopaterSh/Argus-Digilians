# Contract: SelfHealingService

**Module**: `app/tools/self_heal.py`

---

## Interface

```python
class SelfHealingService:
    def __init__(self, runner): ...
    def system_self_heal(self, tool_info: str) -> str: ...
    def health_check(self) -> dict: ...
    def restart_service(self, name: str) -> str: ...
```

## Behaviour

| Method | Condition | Result |
|--------|-----------|--------|
| `health_check()` | All services healthy | `{"wsl": "ok", "ollama": "ok", "python": "ok"}` |
| `health_check()` | Ollama not responding | `{"wsl": "ok", "ollama": "failed: ...", "python": "ok"}` |
| `restart_service("ollama")` | Ollama process found | Kills and restarts Ollama → success message |
| `restart_service("ollama")` | Ollama not installed | Failure message with instructions |
| `restart_service("wsl")` | Kali distro exists | Terminates and re-initializes WSL bridge |
| `restart_service("unknown")` | Unknown name | `"Unknown service: unknown"` |
| `system_self_heal("pip install x")` | Pip succeeds | `"Successfully installed Python package: x."` |

## Test Contract

- Test health_check with each service ok/failed
- Test restart_service with valid and invalid names
- Test system_self_heal pip and apt paths
- Test timeouts on unresponsive services (mock)
