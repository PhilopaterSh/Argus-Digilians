---

description: "Task list for Reflective Verification Hardening"
---

# Tasks: Reflective Verification Hardening

---

## Phase 1: US1 — Infinite-Loop Prevention (Priority: P1)

- [ ] T001 Add in-memory command history tracking to `ReflectiveVerificationService` in `app/tools/reflective_verification.py`
- [ ] T002 Implement loop detection in `pre_execute_verify()`: block if 3+ identical consecutive commands
- [ ] T003 Keep history limited to last 10 entries

---

## Phase 2: US2 — LangChain Tool Exposure (Priority: P1)

- [ ] T004 Add `verify_command()`, `verify_output()`, `assess_difficulty()` delegation methods to `WSLBridgeTools` in `app/tools/tool_registry.py`
- [ ] T005 Register verification tools in `_register_defaults()`

---

## Phase 3: US3 — Test Coverage (Priority: P2)

- [ ] T006 Create `tests/test_tools/test_reflective_verification.py`
- [ ] T007 Write tests for `pre_execute_verify` (empty, blacklist, infinite-loop, valid, nmap/curl validation)
- [ ] T008 Write tests for `post_execute_verify` (WAF, redirect, FP, sensitive data)
- [ ] T009 Test empty/edge inputs

---

## Phase 4: Polish

- [ ] T010 Run test suite + commit
