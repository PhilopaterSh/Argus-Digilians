# Implementation Plan: SQLite Blackboard (ArgusMemory)

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-29 | **Spec**: `specs/003-sqlite-blackboard/spec.md`

---

## Summary

Refactor `app/core/memory/memory_service.py` to add connection safety, error handling, type hints, database migration (consolidate to single file), and comprehensive unit tests. Current code opens/closes a new connection per method with no error handling. This plan makes it production-ready.

---

## Technical Context

**Language/Version**: Python 3.12+

**Current Files**:
| File | Size | Purpose |
|------|------|---------|
| `app/core/memory/memory_service.py` | 7.8 KB | ArgusMemory class (220 lines) |
| `data/argus_intelligence.db` | 56 KB | Live database (3 targets, 23 findings) |
| `argus_intelligence.db` (root) | 13.3 MB | Legacy database (78K targets) |

**Target State**:
| File | Purpose |
|------|---------|
| `app/core/memory/__init__.py` | Package init |
| `app/core/memory/memory_service.py` | Refactored ArgusMemory (WAL, ctx manager, type hints) |
| `data/argus_intelligence.db` | Single canonical database |
| `tests/test_memory.py` | Full test suite |

**Key Design Decisions**:
1. **Context manager for connections**: Each method uses `with self._get_conn() as conn:` to ensure proper cleanup.
2. **WAL mode**: Enabled on first connection for concurrent safety.
3. **Single path**: Remove the constructor parameter, hardcode `data/argus_intelligence.db`.
4. **Migration**: On first init, check for root `argus_intelligence.db` and merge data.
5. **Type hints**: Full `-> int | None` annotations on all methods.
6. **Error handling**: Wrap all DB operations in try/except with logging.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| Migration logic for root DB | Users have accumulated data in two locations | Ignoring root DB would lose 78K targets |

---

## Execution Order

1. Add `__init__.py` to `app/core/memory/`
2. Refactor `memory_service.py` (WAL mode, context manager, type hints, error handling)
3. Add migration logic (merge root DB → data/ DB)
4. Verify existing consumers still work (brain.py, tool_registry.py, etc.)
5. Write `tests/test_memory.py` with full coverage
6. Run migration on actual databases
