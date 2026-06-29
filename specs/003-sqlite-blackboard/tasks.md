# Tasks: SQLite Blackboard (ArgusMemory)

**Input**: Spec at `specs/003-sqlite-blackboard/spec.md`

---

## Phase 1: Foundation

- [ ] T001 Add `app/core/memory/__init__.py` for clean package imports
- [ ] T002 Read and fully understand current `memory_service.py` code

---

## Phase 2: Core Refactor (memory_service.py)

- [ ] T003 Add `_get_conn()` context manager with WAL mode, foreign keys, and timeout
- [ ] T004 Add Python type hints to ALL methods (parameters + return types)
- [ ] T005 Add try/except error handling to all CRUD methods with proper logging
- [ ] T006 Change constructor to hardcode `data/argus_intelligence.db` (remove parameter)
- [ ] T007 Add `_migrate_from_root()` method to merge root DB if it exists
- [ ] T008 Add `_verify_integrity()` method using `PRAGMA integrity_check`
- [ ] T009 Add schema versioning via `schema_version` table + `_get_schema_version()` / `_set_schema_version()`
- [ ] T010 Simplify `add_finding()` to use `INSERT OR IGNORE` pattern for target upsert

---

## Phase 3: Tests

- [ ] T011 Create `tests/test_memory.py` with test for ALL CRUD methods
- [ ] T012 Add edge-case tests: duplicate inserts, empty database, non-existent target
- [ ] T013 Add test for migration from root DB
- [ ] T014 Add test for database integrity check
- [ ] T015 Run tests and verify 90%+ coverage

---

## Phase 4: Verification & Cleanup

- [ ] T016 Verify all existing consumers work: `brain.py`, `tool_registry.py`, `reflective_verification.py`, `simulation.py`, `seed_memory.py`
- [ ] T017 Run migration on actual `argus_intelligence.db` (root) → `data/argus_intelligence.db`
- [ ] T018 Delete root `argus_intelligence.db` after successful migration
- [ ] T019 Run health check to confirm system still operational

---

## Commit Strategy

- Commit after EACH completed task (per `Plan.md` §4)
- Pattern: `feat: 003-blackboard - T001 add __init__.py`
