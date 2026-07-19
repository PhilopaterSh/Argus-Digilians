---

description: "Task list for Self-Healing Expansion"
---

# Tasks: Self-Healing Expansion

---

## Phase 1: US1 — Proactive Health Monitoring (Priority: P1)

- [x] T001 Add `health_check()` method to `SelfHealingService` in `app/tools/self_heal.py`
- [x] T002 Implement `_check_wsl()` using subprocess to run `wsl --status`
- [x] T003 Implement `_check_ollama()` via HTTP GET to localhost:11434/api/tags
- [x] T004 Implement `_check_python()` verifying `Argus_venv` and key imports

---

## Phase 2: US2 — Service Restart (Priority: P1)

- [x] T005 Add `restart_service(name)` method to `SelfHealingService`
- [x] T006 Implement `_restart_ollama()` (kill + restart ollama.exe)
- [x] T007 Implement `_restart_wsl()` (terminate + re-init bridge)

---

## Phase 3: US3 — Test Coverage (Priority: P2)

- [x] T008 Write tests for `health_check()` in `tests/test_tools/test_self_heal.py`
- [x] T009 Write tests for `restart_service()` with valid and invalid names

---

## Phase 4: Polish

- [x] T010 Run test suite + commit
