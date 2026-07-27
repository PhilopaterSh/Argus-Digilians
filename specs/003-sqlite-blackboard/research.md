# Research: SQLite Blackboard (ArgusMemory)

**Phase**: 0 - Technical Research | **Date**: 2026-06-29 | **Spec**: `specs/003-sqlite-blackboard/spec.md`

---

## Purpose

Records the Phase 0 research behind making `app/core/memory/memory_service.py` production-ready.
Grounded in `spec.md` (FR-001..006, NFR-001..004), `plan.md` (Key Design Decisions), `tasks.md`
T001-T010, and architecture ADR-1 ("Why SQLite?"). No new requirements are introduced.

---

## Current State Analysis

From `plan.md` Technical Context:

| File | Size | Issue |
|------|------|-------|
| `app/core/memory/memory_service.py` | 7.8 KB (220 lines) | opens/closes a new connection per method; no error handling; no type hints |
| `data/argus_intelligence.db` | 56 KB | live DB (3 targets, 23 findings) |
| `argus_intelligence.db` (root) | 13.3 MB | legacy DB (78K targets) - data fragmentation |

Key issues: two database files (root + `data/`), no concurrency safety, no migrations, no tests.

---

## Decision 1: Concurrency safety - WAL mode

| Option | Pros | Cons |
|--------|------|------|
| A. WAL (Write-Ahead Logging) | Concurrent readers during a write; crash-consistent; supported on Windows/NTFS since SQLite 3.7.0 | Extra `-wal`/`-shm` sidecar files |
| B. Default rollback journal | Simpler | Writer blocks readers; higher corruption risk on crash |

**Decision**: WAL, enabled on first connection.
*Traceability*: `spec.md` FR-002, NFR (crash safety SC-004); `tasks.md` T003; ADR-1.

---

## Decision 2: Connection lifecycle - context manager

| Option | Pros | Cons |
|--------|------|------|
| A. `with self._get_conn() as conn:` per method | Guaranteed commit/close; no leaks | Slight boilerplate |
| B. Long-lived shared connection | Fewer opens | Leak/locking risk across threads |

**Decision**: Option A - a `_get_conn()` context manager with WAL, foreign keys, and a busy timeout.
*Traceability*: `spec.md` FR-003; `plan.md` Key Design Decision 1; `tasks.md` T003.

---

## Decision 3: Single canonical database path

| Option | Pros | Cons |
|--------|------|------|
| A. Hardcode `data/argus_intelligence.db`; migrate + delete the root DB | One source of truth (spec US2) | One-time migration needed |
| B. Keep a constructor path parameter | Flexible | Perpetuates the two-file fragmentation |

**Decision**: Option A. Remove the constructor parameter; `_migrate_from_root()` merges the root DB
if present, then it is deleted after a successful migration.
*Traceability*: `spec.md` FR-001, FR-005, US2, SC-001; `tasks.md` T006-T007, T017-T018.

---

## Decision 4: Integrity and schema versioning

**Decision**: Add `_verify_integrity()` using `PRAGMA integrity_check` to detect corruption
(`database disk image is malformed`), and a `schema_version` table with
`_get_schema_version()` / `_set_schema_version()` for future migrations.
*Traceability*: `spec.md` FR-006, NFR-004; `tasks.md` T008-T009.

---

## Decision 5: Robustness details

**Decision**: full Python type hints on every method; try/except with logging around all CRUD;
`add_finding()` uses `INSERT OR IGNORE` for target upsert (auto-upsert a missing target - spec Edge
Cases); locked-DB handled by the busy timeout (retry).
*Traceability*: `spec.md` FR-004, NFR-002, Edge Cases; `tasks.md` T004-T005, T010.

---

## Alternatives rejected

- **External DB driver / server (Postgres, etc.)** - rejected; ADR-1 chose SQLite for
  zero-configuration and relational support for the knowledge graph; stdlib `sqlite3` is sufficient
  (`spec.md` Assumptions: single-user, one process at a time).

---

## Decision Traceability Summary

| Decision | Spec ref | Tasks | ADR |
|----------|----------|-------|-----|
| 1 WAL | FR-002, SC-004 | T003 | ADR-1 |
| 2 Context manager | FR-003 | T003 | - |
| 3 Single path + migration | FR-001, FR-005, SC-001 | T006-T007, T017-T018 | - |
| 4 Integrity + schema_version | FR-006, NFR-004 | T008-T009 | - |
| 5 Type hints / errors / upsert | FR-004, NFR-002 | T004-T005, T010 | - |

---

## Open Questions

None. All decisions are present in `spec.md`/`plan.md`; this document consolidates them.
