# Research: Tactical Modules Refactoring

**Phase**: 0 — Technical Research | **Date**: 2026-06-29

---

## Current State

### Files in `app/modules/`

| File | LOC | Issue |
|------|-----|-------|
| `argus_reasoning.py` | 45 | Uses `from core.agent import ArgusBrain` — should be `from app.core.brain import ArgusBrain` |
| `argus_deep_exploit.py` | — | Likely same pattern |
| `stealth_exploit.py` | — | Not read — assumed similar |
| `run_recon.py` | — | Not read |
| `run_full_recon.py` | — | Not read |
| `map_target.py` | — | Not read |
| `seed_memory.py` | — | Not read |
| `ddgs.py` | — | Not read |
| `crawler.py` | — | Not read |
| `check_subs.sh` | — | Shell script — no change needed |
| `__init__.py` | 1 | Only `# Package initialization` — needs `run_all()` |

### Key Observation

All Python files were written before the `app/` prefix was standardized. They reference `core.*` directly, which only works if `PYTHONPATH` includes `app/` or if running from the project root with `python -m app.modules.xxx`.

### Import Pattern to Fix

```
Before:  from core.agent import ArgusBrain
         from core.tools import WSLBridgeTools

After:   from app.core.brain import ArgusBrain
         from app.tools.tool_registry import WSLBridgeTools
```

### Missing Base Class

No module shares a common interface. Each is a standalone function or script. Adding `BaseTacticalModule` enables:
- Uniform `execute(target)` interface
- Registry/orchestration via `run_all()`
- Consistent error handling
- Testability via dependency injection
