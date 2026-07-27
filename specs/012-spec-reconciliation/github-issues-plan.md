# GitHub Issues Mapping Plan (`/speckit.taskstoissues`)

**Canonical reference**: `012-spec-reconciliation`. **Generated**: 2026-07-05.

> The GitHub connector is not authorized in this session, so issues cannot be created here.
> This is the ready-to-execute plan: run it once GitHub is connected (via claude.ai
> connector settings, or `gh issue create` / the GitHub MCP). Only **open** work is listed;
> completed phases (`001`, `003`, `005`–`009`, `013`) are not turned into issues.

## Milestones

| Milestone | Meaning | Contains |
|---|---|---|
| `M1: Reconciled Core` | Code matches `012` canonical design | EPIC-A, EPIC-B, EPIC-C |
| `M2: Canonical Agent + RAG MVP` | `010` implemented on reconciled base | EPIC-D, EPIC-E |
| `M3: Unified GUI` | `011` dashboard on the canonical agent | EPIC-F |
| `M4: CI/CD + Eval` | `012` §6/§7 automated and gating | EPIC-G |

## Labels

`type:epic`, `type:task`, `area:rag`, `area:agent`, `area:gui`, `area:memory`, `area:installer`, `area:ci`, `area:docs`, `priority:P0..P3`, `superseded`, `blocked`.

## Epics → Issues (with dependencies)

### EPIC-A — Converge code to canonical naming (M1, P0) — source: `012` T025–T028
- **A1** Remove duplicate RAG modules (`processor/vectorstore/engine.py`) after callers switch to canonical. `area:rag priority:P0`. Blocks: A-none. Blocked by: A4.
- **A2** Consolidate Brain → single `app/core/agent/brain.py`; delete `brain_v2.py`, `app/core/brain.py`. `area:agent priority:P0`. Blocked by: A4.
- **A3** Consolidate factory → `app/core/agent/agent_factory.py`; delete `_v2`/root shadows. `area:agent priority:P0`. Blocked by: A4.
- **A4** Migrate `app/core/workflow/` (parser, hooks, prompts, capability probe) into `app/core/agent/`, then delete `workflow/`. `area:agent priority:P0`.
- **A5** Update all importers/tests to canonical module paths. `area:agent priority:P0`. Blocked by: A1,A2,A3,A4.

### EPIC-B — RAG embedding manifest (M1, P0) — source: `012` T029, ADR-9
- **B1** Implement `store/manifest.json` write in `vector_store.py`. `area:rag priority:P0`.
- **B2** Deterministic rebuild on hash/embedder mismatch in `rag_engine.py`. `area:rag priority:P0`. Blocked by: B1.
- **B3** RAG-disabled degradation when pinned embedder unavailable. `area:rag priority:P0`. Blocked by: B1.
- **B4** Regression test: cross-dimension query is prevented. `area:rag priority:P1`. Blocked by: B2.

### EPIC-C — Config unification (M1, P2) — source: `012` T024, T031
- **C1** `config.yaml` port → 12199. `area:gui priority:P2`. ✅ Done.
- **C2** `get_port.py` fail-safe default → 12199. `area:gui priority:P2`.

### EPIC-D — RAG hardening remainder (M2, P1) — source: `004` T007–T021 (15 open)
- **D1..D15** map 1:1 to the open `004/tasks.md` items (binary-file skip, logging, per-module tests, etc.). `area:rag priority:P1`. Blocked by: EPIC-B.

### EPIC-E — Canonical LangGraph agent (M2, P1) — source: `010` T001–T030 (33 open)
- **E-phase0..5** map to `010/tasks.md` phases (state schema, RAG MVP, nodes, graph+retry, observability, hardening, validation). `area:agent priority:P1`. Blocked by: EPIC-A, EPIC-B.
- Structured-output decoding issue **E-parse** (`012` T030, ADR-13). Blocked by: A4.

### EPIC-F — Unified GUI dashboard (M3, P2) — source: `011` T001–T031 (31 open)
- **F1..F31** map to `011/tasks.md`. `area:gui priority:P2`. Blocked by: EPIC-E (agent must be importable).

### EPIC-G — CI/CD + AI-eval (M4, P1) — source: `012` §7, T020
- **G1** Pipeline: lint (ruff/PSScriptAnalyzer). **G2** mypy. **G3** PowerShell parser gate. **G4** pytest unit+integration+coverage. **G5** AI-eval suite (recall@k, faithfulness, agent-loop termination). **G6** installer `-DryRun` build validation. **G7** spec-validation (no dup numbers, no dangling supersede). **G8** doc-validation (English-only, links, naming vs `012`). `area:ci priority:P1`.

### EPIC-H — Docs hygiene (M1, P3) — source: `012` T021
- **H1** Translate/retire Arabic `converge.md` files (constitution VI). `area:docs priority:P3`.

## Execution notes
- Create milestones and labels first, then epics, then child issues with `Blocked by` cross-links.
- Suggested title format: `[<AREA>] <verb> <object> (<feature-id> T<nn>)`.
- Each issue body: **Context** (link to spec §), **Acceptance** (from the task/FR), **Canonical ref** (`012` §), **Dependencies**.
