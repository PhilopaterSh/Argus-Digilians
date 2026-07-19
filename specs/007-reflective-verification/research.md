# Research: Reflective Verification Hardening

**Phase**: 0 — Technical Research | **Date**: 2026-06-29

---

## Current State

`ReflectiveVerificationService` in `app/tools/reflective_verification.py` (188 lines):

### Methods

| Method | Lines | Purpose | Issues |
|--------|-------|---------|--------|
| `pre_execute_verify(command)` | 36 | Syntax validation, blacklist, arg checks | Line 49: TODO for infinite-loop via blackboard |
| `post_execute_verify(url, command, raw_output)` | 52 | WAF detection, FP detection, sensitive data | Clean |
| `task_difficulty_assessment(targets)` | 83 | TDA scoring (0-10) | Clean |

### Integration

- Used internally by `WSLBridgeTools`? Let me check...

Actually, looking at `tool_registry.py`, I don't see `ReflectiveVerificationService` being imported or instantiated there. The `self_heal.py` is imported but not `reflective_verification.py`. That means it's only used by whatever code imports it directly.

### Issues to Fix

1. **Line 49 TODO**: `# We can implement a check using the blackboard, or let it pass with validation`
2. **No Tool exposure**: Not listed as a LangChain Tool in GUI or argus_reasoning.py
3. **No tests**
4. **Missing from WSLBridgeTools facade**: Not imported or delegated in `tool_registry.py`

### Infinite-Loop Detection Design

```python
# Track command history via blackboard
COMMAND_HISTORY_KEY = "reflective_verification:command_history"

def pre_execute_verify(self, command: str) -> str:
    # ... existing checks ...
    
    # New: Infinite-loop prevention
    history = self._get_command_history()
    history.append(command)
    if len(history) >= 3 and all(c == command for c in history[-3:]):
        return "Verification Blocked: Command repeated 3+ times (possible infinite loop)."
    
    self._save_command_history(history[-10:])  # Keep last 10
```
