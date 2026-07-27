# Feature Specification: SQLite Blackboard (ArgusMemory)

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-29

**Status**: Implemented (tasks 19/19 complete; `ArgusMemory` present at `app/core/memory/memory_service.py`; verified 2026-07-05). Canonical memory owner per `012` §2.3.

**Input**: Refactor the `ArgusMemory` class in `app/core/memory/memory_service.py` to be production-ready: add connection pooling, error handling, type hints, unit tests, database migration support, and consolidate to a single database location.

---

## User Scenarios & Testing

### User Story 1 - Reliable Persistence (Priority: P1)

As a user, I want the blackboard to survive partial failures and tool crashes without data corruption, so intelligence is never lost.

**Why this priority**: Core reliability — losing findings during a pentest is unacceptable.

**Independent Test**: Kill the Python process mid-write, restart, and verify the database is not corrupted and data is readable.

**Acceptance Scenarios**:

1. **Given** Argus is writing a finding, **When** the process crashes, **Then** the database should remain consistent (no half-written rows).
2. **Given** the database is large, **When** Argus reads the blackboard summary, **Then** it should complete in under 1 second.

---

### User Story 2 - Single Database Location (Priority: P1)

As a developer, I want exactly one database file at `data/argus_intelligence.db`, so there is no confusion about which file contains the live data.

**Why this priority**: Currently two database files exist (root + `data/`), causing data fragmentation.

**Independent Test**: Run `Find-Item -Name "argus_intelligence.db"` — only one file should exist.

**Acceptance Scenarios**:

1. **Given** the old root `argus_intelligence.db` exists, **When** the app starts, **Then** it should migrate data to `data/argus_intelligence.db` and delete the root file.
2. **Given** the app runs, **When** it writes data, **Then** it should always write to `data/argus_intelligence.db`.

---

### User Story 3 - Test Coverage (Priority: P2)

As a developer, I want unit tests for all `ArgusMemory` methods, so regressions are caught immediately.

**Why this priority**: The memory layer is consumed by 5+ modules — breakage propagates everywhere.

**Independent Test**: Run `python -m pytest tests/test_memory.py` and see 100% pass rate.

**Acceptance Scenarios**:

1. **Given** the memory module, **When** tests run, **Then** all CRUD methods should be tested (upsert_target, add_finding, upsert_entity, add_relation, get_blackboard_summary, get_graph_insights, clear_memory).
2. **Given** edge cases, **When** tested, **Then** duplicate inserts, missing targets, and empty database should be handled gracefully.

---

### Edge Cases

- What happens when the database file is locked by another process? — Retry with timeout.
- What happens when a finding references a non-existent target? — Auto-upsert the target.
- What happens when `clear_memory()` is called while other threads are reading? — Thread-safe WAL mode.
- What happens with Unicode/emoji in findings? — SQLite handles UTF-8, verify round-trip.
- What happens when the database grows to 1GB+? — Query performance should degrade gracefully; add indexes.

---

## Requirements

### Functional Requirements

- **FR-001**: ArgusMemory MUST use a single, consistent database path (`data/argus_intelligence.db`).
- **FR-002**: ArgusMemory MUST use WAL (Write-Ahead Logging) mode for concurrent read/write safety.
- **FR-003**: ArgusMemory MUST use a context manager (`with` block) for each connection, ensuring proper close/commit.
- **FR-004**: All CRUD methods MUST include try/except with meaningful error messages.
- **FR-005**: A migration function MUST merge data from root `argus_intelligence.db` into `data/argus_intelligence.db` if both exist.
- **FR-006**: ArgusMemory MUST detect and handle database corruption (e.g., `database disk image is malformed`).

### Non-Functional Requirements

- **NFR-001**: `get_blackboard_summary()` must return in under 500ms for up to 10,000 findings.
- **NFR-002**: All methods must have Python type hints.
- **NFR-003**: Test coverage must be >= 90% for `memory_service.py`.
- **NFR-004**: Database schema versioning via a `schema_version` table for future migrations.

### Key Entities

- **`app/core/memory/memory_service.py`**: The `ArgusMemory` class (refactored).
- **`app/core/memory/__init__.py`**: Package init for clean imports.
- **`data/argus_intelligence.db`**: The single canonical database file.
- **`tests/test_memory.py`**: Unit tests for all methods.

---

## Success Criteria

- **SC-001**: Only ONE database file exists after migration.
- **SC-002**: All existing tools (brain, tool_registry, reflective_verification, simulation) continue to work without code changes.
- **SC-003**: `pytest tests/test_memory.py` passes with 90%+ coverage.
- **SC-004**: Killing the process mid-write never corrupts the database (tested 3x).
- **SC-005**: Blackboard summary for 10K findings returns in under 500ms.

---

## Assumptions

- Python 3.12+ with standard library `sqlite3` (no external DB driver needed).
- WAL mode is supported on Windows/NTFS (yes, since SQLite 3.7.0).
- The database is single-user (one Python process at a time), WAL handles this safely.
