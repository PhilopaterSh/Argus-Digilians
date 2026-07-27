# Tasks: Spec Consolidation & Architecture Reconciliation

**Input**: `specs/012-spec-reconciliation/spec.md`, `specs/012-spec-reconciliation/plan.md`

**Goal**: one consistent, executable, maintainable spec set. Documentation only.

---

## Phase 0 — Numbering

- [x] T001 Rename `specs/003-langgraph-workflow/` → `specs/013-langgraph-workflow/` (resolve duplicate `003`).
- [x] T002 Fix internal self-references (spec/plan/tasks headers and paths) in `013`.

## Phase 1 — Canonical authority

- [x] T003 Author `012` spec (naming, embedding §3, agent §4, parsing §5, testing §6, CI/CD §7).
- [x] T004 Author `012` plan (source-of-truth map, supersession map, phases).
- [x] T005 Author `012` tasks (this file).

## Phase 2 — Supersession headers

- [x] T006 Add "Partially Superseded By" header to `013` spec/plan/tasks.
- [x] T007 Add "Refined By 012 §3" header to `001` spec.
- [x] T008 Add "Refined By 012 §3" header to `004` spec.
- [x] T009 Update `005` spec Input (brain_v2 consolidated per `012` §2.2).
- [x] T010 Add canonical/name-alignment header to `010` spec + plan.

## Phase 3 — Embedding manifest design

- [x] T011 Rewrite `001` FR-005..007 to one-embedder-per-index + manifest + rebuild-on-change (build-time-only fallback; RAG-disabled on mismatch).
- [x] T012 Update `001` plan Complexity Tracking + Key Design Decisions (manifest).
- [x] T013 Update `004` spec FR-001/FR-002 to reference `manifest.json` as the integrity artifact.

## Phase 4 — Naming / chunking / agent alignment

- [x] T014 Align `010` plan module names (`processor→document_processor`, `vectorstore→vector_store`, `engine→rag_engine`; add `config.py`, `embeddings.py`).
- [x] T015 Align `010` tasks module names to canonical.
- [x] T016 Note structural chunking as canonical in `010` (RecursiveCharacterTextSplitter = fallback).

## Phase 5 — Architecture document

- [x] T017 Update ADR-9 (embedding manifest) in `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`.
- [x] T018 Add ADR-13 (structured-output parsing), ADR-14 (canonical naming + single Brain), ADR-15 (canonical agent topology), ADR-16 (unified port).
- [x] T019 Standardize Python `3.12`, port `12199`, single `ArgusBrain`, tool count `17` in the architecture doc.

## Phase 6 — Future (out of scope for this documentation pass)

- [x] T020 Author a `ci-cd` plan doc/YAML implementing `012` §7. **Done:** `.github/workflows/ci.yml` implements the full plan (deterministic BLOCKING jobs: spec/doc validation, lint/type, build-validation, unit-tests; non-blocking full-tests/ai-eval for jobs needing live Ollama/WSL).
- [x] T021 Translate/retire Arabic `converge.md` files for English-only compliance (constitution VI). **Done:** translated all 8 files (`specs/{001-rag-integration,002-consolidated-installer,003-sqlite-blackboard,005-tool-registry,006-tactical-modules,007-reflective-verification,008-self-healing,009-gui}/converge.md`) to English. `scripts/validate_ascii.py` passes (130 files scanned, ASCII/English-only).
- [x] T022 Implement `010` against the reconciled design; migrate `app/core/workflow/` into `app/core/agent/`. **T028 (the workflow migration half) done above.** The canonical tactical agent graph (`build_tactical_graph`, node-based recon->scanner->exploit->reflective/self_heal->post_exploit pipeline) already exists in `app/core/agent/graph.py`/`nodes/*` from a prior session (commit "Implement tactical agent MVP") - `010`'s own `tasks.md` checkboxes are stale bookkeeping, not an accurate reflection of missing work; left as a documentation follow-up (see completion report), not re-implemented here.

## Phase 7 — Convergence gap register (code vs canonical; discovered 2026-07-05)

Code inspection found physical drift: the repo contains BOTH canonical and superseded
files side by side. These tasks close the code↔`012` gap (implementation work; specs
already reconciled). Add-only — no completed task is recreated.

- [x] T024 `config.yaml` `streamlit.port` corrected `8199` → `12199` (ADR-16). ✅ Done.
- [x] T025 Remove duplicate RAG modules (`processor.py`, `vectorstore.py`, `engine.py`); keep `document_processor.py` / `vector_store.py` / `rag_engine.py` (`012` §2.1). **Done:** confirmed no importers (`app/core/rag/__init__.py` and all callers already used the canonical names), physically deleted the three shim files. `app/core/rag/` package still compiles clean.
- [x] T026 Consolidate Brain: merge `app/core/agent/brain_v2.py` (`ArgusBrainV2`) + `app/core/brain.py` (`ArgusBrain`) into a single `app/core/agent/brain.py`; delete the shadow files (`012` §2.2, ADR-14). **Done:** moved `ArgusBrain` to `app/core/agent/brain.py`, added `dispatch()`/`get_available_tools()`/`get_tool_names()` (the `ArgusBrainV2` surface, adapted to `ArgusBrain`'s LangChain `Tool` map), deleted `brain_v2.py`, repointed all importers. `pytest -q` green (124 passed).
- [x] T027 Consolidate factory: merge `app/core/agent/agent_factory_v2.py` + `app/core/agent_factory.py` into `app/core/agent/agent_factory.py`; delete shadows. **Done:** moved `build_agent_executor` to `app/core/agent/agent_factory.py`, deleted `agent_factory_v2.py` (its `create_brain`/`build_tactical_agent` were pure redirects to `build_tactical_graph`, already callable directly), repointed `app/core/agent/brain.py`'s internal import. `pytest -q` green.
- [x] T028 Migrate reusable parts of `app/core/workflow/` (parser, hooks, prompts, capability probe) into `app/core/agent/`, then remove `app/core/workflow/` (`013` retained-scope; `012` §2.2). **Done:** `graph.py`/`state.py`/`prompts.py` moved to `app/core/agent/{react_workflow,react_state,react_prompts}.py` (renamed to avoid clashing with the existing tactical `app/core/agent/graph.py`), exported via `app/core/agent/__init__.py`. `hooks.py` was NOT migrated - confirmed dead code, fully superseded by the inline `pre_hook`/`post_hook` closures already in `graph.py`. Repointed `tests/test_langgraph_workflow.py` and 3 workspace scratch scripts. `pytest -q` green (124 passed).
- [x] T029 Implement `app/core/rag/store/manifest.json` (embedder name/provider/dimension + knowledge_base hash + schema_version) in `vector_store.py`; wire deterministic rebuild in `rag_engine.py` (`012` §3, ADR-9). **Done:** `VectorStore.build_index()` now calls `write_manifest()` (dimension read off `self._store.index.d`, provider/name from a new `EmbeddingFactory.get_provider()`/`get_model_name()` that track which of Ollama/HuggingFace/OpenAI actually got selected). `VectorStore.load_index()` calls `needs_rebuild()` first and additionally cross-checks the manifest's pinned provider against the currently-active one, so a silent Ollama-to-HuggingFace fallback (different dimension, same configured name) is caught too - either mismatch skips the stale load and returns `False`, which `RAGEngine.initialize()` already treats as "must rebuild"; if rebuild also yields 0 chunks, `RAGEngine` naturally serves blackboard-only context via its existing empty-results fallback. Validated with 5 new mocked unit tests (`tests/test_rag/test_vector_store_manifest.py`) since live Ollama/HuggingFace downloads aren't available in this environment - `pytest -q` green (129 passed).
- [x] T030 Implement Ollama `format=json` structured decoding as primary Action path; keep regex parser as fallback (`012` §5, ADR-13). **Done:** added `_ArgusAction` (pydantic model: `thought`/`tool`/`input`/`final_answer`) and `_try_structured_action()` to `app/core/agent/react_workflow.py`. `agent_node` now tries `llm.with_structured_output(_ArgusAction)` first (FR-C9); on success it synthesizes a canonical `Action: {"name":...,"input":...}` / `Final Answer:` string so the existing regex parser in `parse_node` consumes it unchanged (no parse_node changes needed). Any failure (model lacks `with_structured_output`, or it raises) falls back to plain `llm.invoke()` + the original regex parser (FR-C10), same as before this change. 5 new tests in `tests/test_langgraph_workflow.py` cover both paths and the exception fallback; full suite green (134 passed).
- [x] T031 `get_port.py` rewritten with a fail-safe default of `12199` (`012` §2.6); ✅ Done and validated (normal → 12199, missing-config → 12199).

## Phase 8 — Newly discovered (2026-07-05): non-ASCII / mixed-language in first-party code

Constitution VI requires ASCII-safe console/log output and no mixed-language files.
A scan of `app/`, `scripts/`, `tests/` found 26 files with non-ASCII bytes. Classified:
mostly emoji/symbols in log/report strings (cosmetic, valid UTF-8, runs today), plus
**Arabic text in 3 GUI files** (`app/GUI/app.py`, `gui_app.py`, `gui_root.py` — two are
already deprecated per `009`/`011`). NOT fixed in this environment: mass-editing working
/ deprecated code and altering output strings cannot be safely validated here (no test
runtime; deprecated files pending removal). Requires a dev environment with the test suite.

- [x] T032 Removed all non-ASCII from first-party code (24 files + `test_cd.bat`): emoji/box-drawing/arrows/dashes/Kali-prompt symbols -> ASCII equivalents; `config.yaml` `§` -> `sec`. **0 non-ASCII bytes** remain in `app/`, `scripts/`, `tests/` (`.py/.bat/.ps1/.sh`). Intentional Unicode round-trip data in `tests/test_memory.py` preserved as `\uXXXX` escapes (identical runtime values). All cleaned files `py_compile` OK. ✅ Done 2026-07-05.
- [x] T033 Arabic converted to English: the 3 `# تصميم بسيط واحترافي` comments in `app/GUI/{app,gui_app,gui_root}.py` -> `# Simple, professional design`. Corrupted UTF-16 `tests/test_cd.bat` reconstructed as ASCII. ✅ Done 2026-07-05. **Update 2026-07-06**: `gui_app.py`/`gui_root.py` (2 of the 3 files this task touched) have since been deleted entirely - both executed `brain.ask()` unconditionally at import time (unsafe, crashes without a live Ollama/WSL), were 98% duplicates of each other, and were fully superseded by `app/GUI/dashboard.py`. The "full removal tracked with `011`" note is now resolved for these two; `app.py` remains a deprecated-but-safe shim.

## Out of Scope (explicit)

- [ ] T023 Any authorization / allow-list / human-in-the-loop / target-validation mechanism — intentionally excluded from this effort.
