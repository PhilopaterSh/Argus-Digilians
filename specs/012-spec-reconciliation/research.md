# Research: Spec Consolidation & Architecture Reconciliation

**Phase**: 0 - Technical Research | **Date**: 2026-07-05 | **Spec**: `specs/012-spec-reconciliation/spec.md`

---

## Purpose

This document records the Phase 0 research behind the canonical decisions in `spec.md`.
Unlike a greenfield feature, the "research" here is a comparison of the *already-existing*
variants found across specs `001`-`011`/`013` and the selection of one canonical option
per concern, each supported by a technical reason. No new concepts are introduced; every
option below was already present in the project before consolidation.

---

## Current State Analysis (drift inventory)

### Competing variants found

| Concern | Variant A (found in) | Variant B (found in) | Variant C (found in) |
|---------|----------------------|----------------------|----------------------|
| RAG module names | `document_processor.py` / `vector_store.py` / `rag_engine.py` (`001`, `004`, arch, `005`) | `processor.py` / `vectorstore.py` / `engine.py` (`010`) | - |
| RAG chunking | Structural per-format (`001`, `004`) | Linear `RecursiveCharacterTextSplitter` only (`010`) | - |
| Embedding fallback | Query-time Ollama->HF->OpenAI across 768/384/1536 dims (`001` FR-005..007) | (implied) build-time selection (`004`, arch) | - |
| Agent topology | Generic dual-mode ReAct in `app/core/workflow/` (`013`) | Explicit node graph in `app/core/agent/` (`010`) | - |
| Brain | `app/core/brain.py` `ArgusBrain` (`001`, `013`) | `app/core/agent/brain_v2.py` `ArgusBrainV2` (`005`) | node graph reasoning (`010`) |
| Factory | `app/core/agent_factory.py` | `app/core/agent/agent_factory_v2.py` (`005`) | - |
| Streamlit port | `8199` (`013` / `config.yaml`) | `8501` (`get_port.py` fail-safe) | `12199` (`011`) |
| Python version | `3.10+` (`001`, `013`) | `3.12` (`003-sqlite`, `004`, `005`, `006`, `010`) | - |
| Tool-output parsing | Regex JSON->text dual parser (`013`) | (none structured) | - |
| Registered-tool count | "12" (arch) | "14" (`005`) | "17" actual (14 + 3 from `007`) |

### Key issues

1. **Numbering collision** - two features share `003` (`003-langgraph-workflow`, `003-sqlite-blackboard`).
2. **No supersession markers** - `010` silently redesigns what `001`/`004`/`013` already shipped.
3. **A runtime-incorrect embedding design** - a FAISS index has fixed dimensionality; a query-time fallback to a different-dimension model raises a dimension-mismatch error, not a graceful fallback.
4. **Physical code duplication** - the repo contains both naming sets and both agent designs side by side.
5. **Config drift** - three ports, two Python versions, three tool counts.

---

## Decision 1: RAG module naming and chunking

| Option | Pros | Cons |
|--------|------|------|
| A. `document_processor` / `vector_store` / `rag_engine` + structural chunking | Descriptive; already implemented and hardened; used by 4 documents incl. the architecture source of truth | Slightly longer names |
| B. `processor` / `vectorstore` / `engine` + linear chunking only | Shorter | Used by 1 (Draft) doc; loses per-format semantic chunking; forces mass rename of 4 documents |

**Decision**: Option A. Descriptive names already dominate the documentation set and are clearer
for maintenance/DX; structural chunking preserves semantic boundaries better than fixed-size,
with `RecursiveCharacterTextSplitter` retained as the plain/unknown-format fallback.
*Traceability*: `spec.md` section 2.1.

---

## Decision 2: Embedding / index integrity (the correctness fix)

| Option | Behavior | Risk |
|--------|----------|------|
| A. Query-time fallback across dims (original `001`) | Swap embedder on the fly | **Fails** - FAISS dimension mismatch at query time |
| B. One embedder per index + `manifest.json`, build-time-only fallback, RAG-disabled on mismatch | Deterministic; honest degradation | None known; requires a rebuild on embedder change |

**Decision**: Option B. The fallback chain runs only at build time to pick an available embedder,
which is pinned in `app/core/rag/store/manifest.json` (name, provider, dimension, knowledge_base
hash, built_at, schema_version). If the pinned embedder is unavailable at query time and no rebuild
is possible, RAG degrades to Blackboard-only rather than issuing an invalid query. This preserves the
non-blocking guarantee (`001` FR-010) without the defect and doubles as the FAISS staleness artifact
required by `004` FR-002.
*Traceability*: `spec.md` section 3 (FR-C1..C5); Architecture ADR-9.

---

## Decision 3: Canonical agent topology

| Option | Pros | Cons |
|--------|------|------|
| A. Generic dual-mode ReAct (`013`, `app/core/workflow/`) | Model-agnostic; already built | Open-ended loop; harder to bound/observe for an offensive agent |
| B. Explicit node graph Recon->Scanner->Exploit<->Reflective->Post-Exploit (`010`, `app/core/agent/`) | Bounded (`MAX_RETRIES` + recursion limit); one structured event per transition; domain-aligned; truthful runtime | Domain-specific (by design) |

**Decision**: Option B is the canonical production agent. Option A's reusable mechanisms - the
tool-calling capability probe, the Action parser, and the pre/post model hooks - are retained and
migrate from `app/core/workflow/` into `app/core/agent/`. `ArgusBrain` is the reasoning callee used
by nodes, not a competing orchestrator.
*Traceability*: `spec.md` section 4 (FR-C6..C8); Architecture ADR-12, ADR-15.

---

## Decision 4: Single Brain and single Factory

| Option | Pros | Cons |
|--------|------|------|
| A. Keep `brain.py` + `brain_v2.py` + `agent_factory.py` + `agent_factory_v2.py` | No refactor now | Four overlapping controllers; `_v2` shadow files rot (violates SRP) |
| B. One `app/core/agent/brain.py` (`ArgusBrain`) + one `agent_factory.py` | One unambiguous name per concept | Requires a guarded merge with test migration |

**Decision**: Option B. `ArgusBrainV2`'s registry-dispatch capability merges into the single
`ArgusBrain`; the `_v2` names are Deprecated / Replaced By the non-suffixed canonical modules.
*Traceability*: `spec.md` section 2.2; Architecture ADR-14.

---

## Decision 5: Tool-output parsing

| Option | Pros | Cons |
|--------|------|------|
| A. Regex JSON->text dual parser (`013`) | Works with any text model | Brittle; whole class of parse failures |
| B. Structured decoding (`format=json` / native `tool_calls`), regex as fallback | Reliable Action extraction; fewer retries | Requires a model that honors `format=json` (fallback covers the rest) |

**Decision**: Option B primary, Option A fallback.
*Traceability*: `spec.md` section 5 (FR-C9..C10); Architecture ADR-13.

---

## Decision 6: Runtime constants

| Constant | Options | Decision | Reason |
|----------|---------|----------|--------|
| Streamlit port | 8199 / 8501 / 12199 | **12199** | Newest professional dashboard spec (`011`) asserts it in its acceptance tests; fail-safe default set equal to it to make drift impossible |
| Python version | 3.10+ / 3.12 | **3.12** | Deployment venv is 3.12 (arch section 7); majority of specs already use it |
| Registered-tool count | 12 / 14 / 17 | **17** | 14 core + 3 reflective-verification tools added in `007` (confirmed by `specs/checklist.md`) |

*Traceability*: `spec.md` section 2.6; Architecture ADR-16.

---

## Decision 7: Numbering collision resolution

**Decision**: rename `003-langgraph-workflow` -> `013-langgraph-workflow`. `003-sqlite-blackboard`
(created 2026-06-29) predates the LangGraph feature (2026-07-05) and is the feature other specs
reference as "Phase 003" (e.g., `004`/`005` cite `tests/test_memory.py` from Phase 003), so the
LangGraph workflow is the accidental duplicate and is renumbered.
*Traceability*: `spec.md` FR-001; `tasks.md` T001-T002.

---

## Decision 8: Testing and CI/CD standardization

| Area | Prior state | Decision |
|------|-------------|----------|
| Test tiers | Ad hoc unit tests per feature; no eval; "CI" referenced but undefined | Adopt a unit/integration/e2e/AI-evaluation/regression/performance pyramid (`spec.md` section 6) |
| CI pipeline | Manual syntax + dry-run gates (constitution) | Automate the same gates plus lint/type/spec/doc validation (`spec.md` section 7) |

**Decision**: Standardize both across all features; the constitution's manual gates become the
automated stages 3 and 6. AI-evaluation closes the previously-unfalsifiable "reduces hallucination"
claims.
*Traceability*: `spec.md` sections 6-7; Constitution v1.1.0 "Testing & AI-Evaluation gate".

---

## Alternatives considered and rejected

- **Delete superseded specs outright** - rejected; Spec-Kit history is retained with resolving
  headers (`Superseded By` / `Refined By` / `Replaced By`) so decisions remain auditable.
- **Adopt `010`'s short module names** - rejected per Decision 1 (higher churn, less descriptive).
- **Keep query-time embedder fallback but catch the error** - rejected; it silently disables RAG
  on every fallback and hides the root cause; the manifest design is deterministic instead.

---

## Decision Traceability Summary

| Decision | Spec ref | Architecture ADR | Tasks |
|----------|----------|------------------|-------|
| 1 RAG names/chunking | 2.1 | ADR-14 | - |
| 2 Embedding manifest | 3 | ADR-9 | T029 |
| 3 Agent topology | 4 | ADR-12, ADR-15 | T028 |
| 4 Single Brain/Factory | 2.2 | ADR-14 | T026, T027 |
| 5 Structured parsing | 5 | ADR-13 | T030 |
| 6 Runtime constants | 2.6 | ADR-16 | T024, T031 |
| 7 Numbering | FR-001 | - | T001, T002 |
| 8 Testing/CI-CD | 6, 7 | - | T020 |

---

## Open Questions

None. Every decision above was already made and justified in `spec.md`/`plan.md`; this document
consolidates the rationale. No external input is required to proceed to `data-model.md`.
