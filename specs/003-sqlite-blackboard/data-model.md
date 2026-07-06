# Data Model: SQLite Blackboard (ArgusMemory)

**Phase**: 1 - Design | **Date**: 2026-06-29 | **Spec**: `specs/003-sqlite-blackboard/spec.md`

---

## Purpose

Documents the persistent data model owned by `app/core/memory/memory_service.py` (`ArgusMemory`).
The authoritative DDL lives in `memory_service.py`; the tables and columns below are derived from the
method signatures in `spec.md`, the architecture doc (section 5.1: "SQLite Blackboard with 5 tables
targets, findings, entities, relations, global_state") and the runtime sequence (section 6.1). No
columns beyond those implied by the repository are introduced.

**Canonical database path**: `data/argus_intelligence.db` (single file; `spec.md` FR-001).
**Journal mode**: WAL (`spec.md` FR-002).

---

## Entity 1: targets

The assessed targets. Populated by `upsert_target(domain)` and summarized by
`get_blackboard_summary()` (target IPs, open ports, discovered technologies).

| Column (derived) | Purpose |
|------------------|---------|
| domain / target | Primary key - the target identifier |
| ip | Resolved IP (from summary output) |
| ports | Open ports discovered |
| tech | Discovered technologies |

---

## Entity 2: findings

Structured results of tool runs. Written by
`add_finding(domain, tool, type, raw, summary)` (`spec.md` US3 AC-1; architecture section 6.1).

| Column | Purpose |
|--------|---------|
| target / domain | Foreign key to targets (auto-upserted if missing - Edge Cases) |
| tool | Producing tool (e.g. nmap, nuclei) |
| type | Finding category |
| raw | Raw tool output |
| summary | Structured/parsed summary |

---

## Entity 3: entities

Knowledge-graph nodes. Written by `upsert_entity(...)` (e.g. ip / tech / vuln - architecture 6.1).

| Column (derived) | Purpose |
|------------------|---------|
| type | Entity kind (ip, tech, vuln, ...) |
| value | Entity value/identifier |

---

## Entity 4: relations

Knowledge-graph edges. Written by `add_relation(entity1, entity2, relation)` (e.g. "HOSTS").
Returned by `get_graph_insights()` as entity -> relation -> entity triples.

| Column | Purpose |
|--------|---------|
| entity1 | Source entity |
| entity2 | Target entity |
| relation | Edge label (e.g. HOSTS) |

---

## Entity 5: global_state

Cross-cutting key/value state (architecture section 5.1: fifth table).

| Column (derived) | Purpose |
|------------------|---------|
| key | State key |
| value | State value |

---

## Entity 6: schema_version

Migration bookkeeping (`spec.md` NFR-004; `tasks.md` T009).

| Column | Purpose |
|--------|---------|
| version | Current schema version integer |

---

## Public methods (contract)

From `spec.md` Success Criteria SC-002 and User Story 3:

| Method | Role |
|--------|------|
| `upsert_target(domain)` | Insert/update a target |
| `add_finding(domain, tool, type, raw, summary)` | Record a finding (auto-upserts target) |
| `upsert_entity(...)` | Insert/update a graph entity |
| `add_relation(entity1, entity2, relation)` | Insert a graph edge |
| `get_blackboard_summary()` | Dict of targets, ports, technologies, findings |
| `get_graph_insights()` | Entity -> relation -> entity triples |
| `clear_memory()` | Reset state (thread-safe under WAL) |

---

## Relationships

```text
targets 1---* findings
entities *---* entities (via relations edges)
global_state : standalone key/value
schema_version : single-row migration marker
```

---

## Acceptance Criteria (data model)

- **AC-1**: Exactly one database file exists after migration (`spec.md` SC-001).
- **AC-2**: `get_blackboard_summary()` returns within 500 ms for up to 10,000 findings
  (`spec.md` NFR-001, SC-005) - add indexes as the DB grows (Edge Cases).
- **AC-3**: A finding referencing a non-existent target auto-upserts that target (Edge Cases).
- **AC-4**: Killing the process mid-write never corrupts the database (WAL; `spec.md` SC-004).
- **AC-5**: Unicode/emoji round-trip intact (UTF-8; `spec.md` Edge Cases; verified by
  `tests/test_memory.py`).

---

## Implementation Notes

- Exact column definitions and indexes are owned by `memory_service.py`; this document is the
  conceptual model. If the two ever diverge, `memory_service.py` is the source of truth for DDL and
  this file is updated to match.
- All existing consumers (`brain.py`, `tool_registry.py`, `reflective_verification.py`,
  `simulation.py`, `seed_memory.py`) use these methods unchanged (`spec.md` SC-002; `tasks.md` T016).
