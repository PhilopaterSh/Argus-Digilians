# Data Model: Self-Healing

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Flow

```
Caller (Brain / GUI / Watchdog)
    │
    ▼
SelfHealingService
    │
    ├── system_self_heal(tool_info)  ← Existing (pip/apt install)
    │
    ├── health_check() → dict
    │       ├── _check_wsl()      → "ok" | "failed: <reason>"
    │       ├── _check_ollama()   → "ok" | "failed: <reason>"
    │       └── _check_python()   → "ok" | "failed: <reason>"
    │
    └── restart_service(name) → str
            ├── "ollama" → _restart_ollama()
            └── "wsl"    → _restart_wsl()
```

## Health Check Format

```python
{
    "wsl": "ok" | "failed: timeout" | "failed: not installed",
    "ollama": "ok" | "failed: not responding on :11434",
    "python": "ok" | "failed: Argus_venv not found"
}
```
