# Contract: ReflectiveVerificationService

**Module**: `app/tools/reflective_verification.py`

---

## Interface

```python
class ReflectiveVerificationService:
    def pre_execute_verify(self, command: str) -> str: ...
    def post_execute_verify(self, url: str, command: str, raw_output: str) -> str: ...
    def task_difficulty_assessment(self, targets: str) -> str: ...
```

## Behaviour

| Method | Condition | Result |
|--------|-----------|--------|
| `pre_execute_verify` | Empty command | `"Verification Warning: Command is empty."` |
| `pre_execute_verify` | Blacklist pattern (`rm -rf`) | `"Verification Blocked: ..."` |
| `pre_execute_verify` | 3+ identical commands in a row | `"Verification Blocked: Command repeated 3+ times..."` |
| `pre_execute_verify` | Valid command | `"SUCCESS: Command syntax and parameters validated."` |
| `post_execute_verify` | WAF indicator in output | `"ALERT: Target responded with a WAF block..."` |
| `post_execute_verify` | Sensitive data found | `"SUCCESS: High-severity finding verified. ..."` + blackboard write |
| `post_execute_verify` | No issues | `"Analysis: Command executed successfully..."` |
| `task_difficulty_assessment` | Valid target list | TDA report string with scores |
| `task_difficulty_assessment` | Empty list | `"Error: No targets provided."` |

## Test Contract

- Test each verification condition in pre_execute_verify
- Test infinite-loop: 1st=pass, 2nd=pass, 3rd+=block
- Test each post_execute_verify condition (WAF, redirect, FP, sensitive data)
- Test TDA scoring calculation
- Test empty/edge inputs
