# Quickstart: SQLite Blackboard (ArgusMemory)

**Phase**: 1 - Validation | **Date**: 2026-06-29 | **Spec**: `specs/003-sqlite-blackboard/spec.md`

---

## Purpose

How to validate the refactored `ArgusMemory`. Derived from `spec.md` (Success Criteria SC-001..005,
User Stories), `tasks.md` T011-T019, and `tests/test_memory.py`.

## Prerequisites

- Python 3.12 (canonical per `specs/012-spec-reconciliation` section 2.6).
- Standard-library `sqlite3` only - no external driver (`spec.md` Assumptions).
- Run from the project root.

---

## Check 1: Single database file

```bash
find . -name "argus_intelligence.db" -not -path "./Argus_venv/*"
```

**Expected**: exactly one path, `./data/argus_intelligence.db` (`spec.md` FR-001, SC-001;
`tasks.md` T017-T018).

---

## Check 2: WAL mode active

```bash
python3 -c "import sqlite3; c=sqlite3.connect('data/argus_intelligence.db'); print('journal_mode =', c.execute('PRAGMA journal_mode').fetchone()[0])"
```

**Expected**: `journal_mode = wal` (`spec.md` FR-002).

---

## Check 3: Integrity

```bash
python3 -c "import sqlite3; c=sqlite3.connect('data/argus_intelligence.db'); print('integrity =', c.execute('PRAGMA integrity_check').fetchone()[0])"
```

**Expected**: `integrity = ok` (`spec.md` FR-006; `tasks.md` T008).

---

## Check 4: Schema version present

```bash
python3 -c "import sqlite3; c=sqlite3.connect('data/argus_intelligence.db'); print(c.execute('SELECT version FROM schema_version').fetchone())"
```

**Expected**: a single integer version row (`spec.md` NFR-004; `tasks.md` T009).

---

## Check 5: Unit tests and coverage

```bash
pytest tests/test_memory.py -q
```

**Expected**: all tests pass, covering every CRUD method plus edge cases (duplicate inserts, empty
database, non-existent target, migration, integrity) at 90%+ coverage
(`spec.md` SC-003, NFR-003; `tasks.md` T011-T015).

---

## Check 6: Performance (summary latency)

```bash
python3 -c "import time; from app.core.memory.memory_service import ArgusMemory; m=ArgusMemory(); t=time.time(); m.get_blackboard_summary(); print('summary ms:', round((time.time()-t)*1000,1))"
```

**Expected**: under 500 ms (`spec.md` NFR-001, SC-005). (Requires the runtime environment.)

---

## Check 7: Crash safety (manual)

Start a write, kill the Python process mid-write, restart, and re-open the database.

**Expected**: the database is consistent (no half-written rows), data is readable; repeat 3x
(`spec.md` SC-004, US1).

---

## Validation checklist

| Check | Expected | Source |
|-------|----------|--------|
| Single DB file | only `data/argus_intelligence.db` | SC-001 |
| WAL enabled | `wal` | FR-002 |
| Integrity | `ok` | FR-006 |
| Schema version | one integer row | NFR-004 |
| Tests | pass, 90%+ coverage | SC-003 |
| Summary latency | < 500 ms @ 10K findings | NFR-001, SC-005 |
| Crash safety | no corruption (3x) | SC-004 |

---

## Troubleshooting

- **Database locked**: handled by the connection busy timeout (retry); confirm no other process holds
  a write lock (`spec.md` Edge Cases).
- **Two DB files found**: the root `argus_intelligence.db` was not migrated - re-run initialization
  so `_migrate_from_root()` merges and removes it (`tasks.md` T007, T017-T018).
