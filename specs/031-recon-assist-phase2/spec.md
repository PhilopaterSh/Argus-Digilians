# Feature Specification: Recon-Assist Phase 2 — Pipeline Execution via the Kali Bridge

**Feature ID**: `031-recon-assist-phase2`

**Feature Branch**: `feat/recon-assist-phase2`

**Created**: 2026-11-04

**Status**: Draft

**Input**: Phase 1 (spec 030) landed the read-side bridge: Argus reads the
pipeline's `argus_brief.json` and ingests leads into ArgusMemory. Phase 2
adds the execution side: ArgusBrain can now LAUNCH the differential pipeline
for an authorized domain through the existing Kali WSL bridge, closing the
loop (detect diff → plan → run → ingest → prioritize).

**Companion**: Recon-Assist v2.9.1 (config-driven, scope-guarded, schedule-verified
- run 24 all 10 jobs green). Bridge service: `app/tools/recon_assist_run.py`.

---

## 1. Why this spec exists

Phase 1 made Argus a consumer of recon intelligence. But the differential
edge (community canon 2025: "run on a schedule, act on the diff") requires
the agent to also TRIGGER the pipeline when new scope or a fresh cadence
demands it - without leaving the Argus session. The WSL bridge already
executes everything in Kali; this spec adds one bounded, audited launcher
on top of it.

## 2. Scope

### In scope
- `ReconAssistRunService` (`app/tools/recon_assist_run.py`):
  - `run_differential(domain)` — runs `local_run.sh` for one domain via the
    shared CommandRunner (40-min bounded timeout, audit-logged both ends).
  - `run_status()` — shows the latest local report summary without scanning.
- Domain-format validation BEFORE any command (rejects injection).
- Tool Registry adapters: `recon_assist_run`, `recon_assist_status`.

### Out of scope (N/A at Draft)
- Deep scan / fuzz / dorks from inside Argus (manual layers stay manual).
- Any target NOT in the pipeline's own scope guard (the pipeline re-validates).

## 3. Guardrails (non-negotiable)

1. Domain-format validation before any command construction (no shell
   interpolation of unvalidated input).
2. The pipeline's own scope guard is the authorization boundary — Argus adds
   zero targets of its own.
3. Both run ends are audit-logged via `app/core/audit.log_event`.
4. Bounded 2400s timeout: a wedged run cannot block the agent loop.

## 4. Requirements

- R1: Invalid domains rejected before any execution.
- R2: Both run ends audit-logged (`log_event("command", "agent", domain, ...)`).
- R3: The command must cd into the repo and invoke local_run.sh with the
  bounded stage list (no fuzz/deep in the tool path).
- R4: Tool output = fenced Markdown tail + report path pointer.

## 5. Deliverables on this branch

- `app/tools/recon_assist_run.py` — the run-side service.
- `tests/test_tools/test_recon_assist_run.py` — 4 unit tests.
- Tool Registry wiring (2 adapters).

## 6. Phases

- Phase 1 (spec 030): read-side — DONE, merged.
- Phase 2 (this spec): run-side — THIS BRANCH.
- Phase 3 (future): scheduled agent tasks on the diff; RAG ingestion of
  brief Markdown; report drafting with mandatory human review.
