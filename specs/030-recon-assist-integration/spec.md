# Feature Specification: Recon-Assist Integration (Differential Recon Intelligence)

**Feature ID**: `030-recon-assist-integration`

**Feature Branch**: `feat/recon-assist-integration`

**Created**: 2026-10-31

**Status**: Draft

**Input**: Bridge the Recon-Assist differential reconnaissance pipeline
(github.com/PhilopaterSh/Recon-Assist, v2.6) into Argus as a first-class
intelligence source. The pipeline produces a weekly-diffed `argus_brief.json`
(schema `recon-assist/argus-brief@v1`: new hosts, takeover indicators, JS
secret indicators, ASN/network-owner attribution, priority scoring). Argus
consumes that brief as structured intelligence so ArgusBrain can plan manual
testing on **new/changed assets only**, and ArgusMemory tracks each lead
through its lifecycle (new → triaged → testing → reported).

**Companion repo**: `Recon-Assist` (scripts/export_for_argus.py produces the
brief; scope_guard.py enforces the same authorization roots; weekly schedule
runs the differential already).

---

## 1. Why this spec exists

Recon-assist automation (2025-2026 community canon: coverage-over-heroics,
differential monitoring) produces a stream of **new/changed assets**, but the
winning edge per community research is acting on the diff quickly — fresh DNS
changes are where dangling records appear first. Argus already owns the
reasoning layer (ReAct brain), the memory layer (SQLite blackboard), and the
execution layer (Kali WSL bridge) — the three layers needed to act on that
diff. Today none of them are connected to it. This feature closes that loop
with a **loose-coupling, file-based** integration (no ArgusBrain changes, no
new network services, no new credentials).

## 2. Scope

### In scope
- `ReconAssistBriefService` (host-side, dependency-light: stdlib only) with:
  - `load_brief(brief_path)` — parse `argus_brief.json`, return an
    LLM-facing fenced summary, and ingest into ArgusMemory:
    `upsert_target` per new host, `add_finding` per priority/takeover/secret.
  - `new_hosts(brief_path)` — the diff list.
  - `differential_guidance(brief_path)` — deterministic manual-testing
    guidance text ordered by the brief's priority scores.
- Tool Registry wiring: adapters `recon_brief`, `recon_new_hosts`,
  `recon_guidance` (host-side service — no WSL runner needed for v1).
- Unit tests mirroring `tests/test_tools/test_command_runner.py` conventions.

### Out of scope (explicit N/A at Draft stage)
- Running scans from inside Argus (the pipeline owns scanning; see
  `recon_assist_run` candidate for Phase 2).
- LLM auto-drafting of HackerOne reports (human review is a hard gate).
- Any modification to Recon-Assist or its schedule.

## 3. Guardrails (non-negotiable)

1. The agent **never invents findings** — the brief's deterministic scores
   are authoritative; LLM may re-rank, explain, and plan only.
2. Every brief host is bound by the pipeline's `scope.txt` (the same guard
   that gated its discovery) — Argus adds no targets of its own.
3. JS "secret indicators" are **candidates until manually verified**.
4. No credentials, cookies, tokens, or raw target data are copied into
   ArgusMemory or the KB — only hostnames, verdicts, and scores.

## 4. Requirements

- R1: Brief ingestion MUST be idempotent (re-loading the same brief must not
  duplicate findings or targets).
- R2: Malformed/missing brief files MUST degrade to a clear error string,
  never an exception reaching the agent loop.
- R3: Host extraction MUST accept both bare hosts and httpx-style URL lines.
- R4: Every ingest MUST tag `tool_name="recon_assist"` and the brief's
  generation timestamp for lifecycle tracking.
- R5: The service MUST work host-side (no WSL/SSH dependency) — the brief
  file is written on the host by the pipeline and read on the host by Argus.

## 5. Deliverables on this branch

- `app/tools/recon_assist.py` — the service.
- `tests/test_tools/test_recon_assist.py` — unit tests (ingest idempotency,
  malformed-brief degradation, host extraction, priority ordering).
- Registry wiring in `app/tools/tool_registry.py`.

## 6. Phases

- Phase 1 (this branch): brief ingestion + memory + registry (read-only).
- Phase 2 (future spec): `recon_assist_run` tool — invoke the differential
  scan from Kali via the existing bridge; results flow back through the same
  brief format.
- Phase 3 (future spec): RAG ingestion of brief Markdown; report drafting
  with mandatory human review.
