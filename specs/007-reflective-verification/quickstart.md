# Quickstart: Validating Reflective Verification

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Validation Steps

### 1. Unit Tests

```bash
pytest tests/test_tools/test_reflective_verification.py -v
```

Expected: 15+ tests passing.

### 2. Infinite-Loop Test

```python
from app.tools.reflective_verification import ReflectiveVerificationService
service = ReflectiveVerificationService(runner, memory)

# First call — should pass
r1 = service.pre_execute_verify("nmap -sV example.com")
print(r1)  # SUCCESS

# Second call — should pass
r2 = service.pre_execute_verify("nmap -sV example.com")
print(r2)  # SUCCESS

# Third call — should block
r3 = service.pre_execute_verify("nmap -sV example.com")
print(r3)  # BLOCKED
```

### 3. LangChain Tool Registration

```python
from app.tools.tool_registry import WSLBridgeTools
tools = WSLBridgeTools()

# After feature implementation, these should exist:
print(tools.verify_command("nmap -sV example.com"))
print(tools.verify_output("http://example.com", "nmap -sV", "...output..."))
```
