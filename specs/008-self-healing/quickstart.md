# Quickstart: Validating Self-Healing

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Validation Steps

### 1. Unit Tests

```bash
pytest tests/test_tools/test_self_heal.py -v
```

Expected: 10+ tests passing.

### 2. Health Check Test

```python
from app.tools.self_heal import SelfHealingService
healer = SelfHealingService(runner)
status = healer.health_check()
print(status)  # {"wsl": "ok", "ollama": "ok", "python": "ok"}
```

### 3. Restart Test

```python
result = healer.restart_service("ollama")
print(result)  # "Successfully restarted Ollama" or failure message

result = healer.restart_service("unknown")
print(result)  # "Unknown service: unknown"
```
