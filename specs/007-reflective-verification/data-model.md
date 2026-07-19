# Data Model: Reflective Verification

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Flow

```
Command (from Brain / GUI)
    │
    ▼
pre_execute_verify(command)
    ├── Empty command check
    ├── Blacklist pattern check
    ├── Tool-specific arg validation
    └── Infinite-loop detection ← NEW
            │
            ├── Read command history from blackboard
            ├── Detect 3+ identical consecutive commands
            └── Block if loop detected
    │
    ▼ (if PASS)
Execute command
    │
    ▼
post_execute_verify(url, command, raw_output)
    ├── WAF block detection
    ├── Redirect/FP detection
    ├── Content-Length zero check
    └── Sensitive data confirmation → blackboard.add_finding()
```

## Infinite-Loop State

```
Blackboard key: "reflective_verification:command_history"
Type: list[str] (max 10 entries)
Flow:
  pre_execute_verify → read history → append command → check last 3 → save history[-10:]
```
