# Tasks: LangGraph Agent & LangChain RAG Architecture

**Input**: Updated plan from `/specs/010-langgraph-agent/plan.md`

**Goal**: deliver a reliable MVP first, then harden observability and resilience.

**Status note (2026-07-06)**: this file previously showed 0/33 complete, which did not
reflect reality - the checkboxes had simply never been updated as work landed (commit
"Implement tactical agent MVP" and later sessions). Reconciled against the actual code
below; see each item for evidence. Only T027 and T029 are genuine, real gaps.

## Phase 0: Foundation Alignment

- [x] T001 Define the canonical runtime entrypoints for the Streamlit dashboard and the agent runner. `AGENT_RUNNER_ENTRYPOINT`/`STREAMLIT_DASHBOARD_ENTRYPOINT` in `app/core/agent/contracts.py`; `scripts/run_agent.py` and `app/GUI/dashboard.py` both exist.
- [x] T002 Lock the `AgentState` schema to include durable messages, retry counters, and result fields. `app/core/agent/state.py` - `messages`, `retry_count`, `final_state` all present.
- [x] T003 Define the JSON shape for agent run events and final snapshots. `AgentRunEvent`/`AgentRunSnapshot` TypedDicts + `build_run_event`/`build_run_snapshot` in `contracts.py`.
- [x] T004 Document the production vs demo/test behavior split for fallbacks. `AGENT_RUN_MODE_{PRODUCTION,DEMO,TEST}` + `normalize_run_mode()` in `contracts.py`.

## Phase 1: RAG MVP

- [x] T005 Implement document loading and structural chunk creation in `app/core/rag/document_processor.py` (canonical name per `012` §2.1). `MarkdownHeaderTextSplitter`-based structural split implemented.
- [x] T006 Implement `RecursiveCharacterTextSplitter` as the plain/unknown-format **fallback** in `app/core/rag/document_processor.py` (structural chunking is primary). Confirmed as fallback path.
- [x] T007 Implement Ollama embeddings + FAISS indexing + `store/manifest.json` (one embedder per index, build-time fallback) in `app/core/rag/vector_store.py` (per `012` §3). Manifest wiring completed 2026-07-06 (`012` T029).
- [x] T008 Implement the linear retrieval/query flow (with RAG-disabled degradation on embedder/dimension mismatch) in `app/core/rag/rag_engine.py`. `retrieve()`/`query()` implemented; degrades via `VectorStore.load_index()`'s manifest guard.
- [x] T009 Add a smoke test script for retrieval and answer generation. `tests/test_rag/test_rag_engine_threshold.py`, `test_vector_store_manifest.py`, `test_manifest.py`.

## Phase 2: Tactical Agent MVP

- [x] T010 Implement the recon node without synthetic success data in `app/core/agent/nodes/recon.py`.
- [x] T011 Implement the scanner node with real scan result ingestion in `app/core/agent/nodes/scanner.py`.
- [x] T012 Implement the exploit node with explicit success/failure reporting in `app/core/agent/nodes/exploit.py`.
- [x] T013 Implement the reflective node with real verification/context handling in `app/core/agent/nodes/reflective.py`.
- [x] T014 Implement the post-exploit node to persist final results to the blackboard in `app/core/agent/nodes/post_exploit.py`.
- [x] T015 Compile the LangGraph workflow in `app/core/agent/graph.py` with explicit termination rules and retry bounds. `build_tactical_graph()` with `should_continue()` routing.
- [x] T016 Add a configurable `MAX_RETRIES` / recursion limit guard to the agent graph. `MAX_RETRIES` read from `ArgusConfig.max_retries` (default 3) in `graph.py`.

## Phase 3: Observability and UI

- [x] T017 Write structured run events from the agent runner in `scripts/run_agent.py`. Uses `build_run_snapshot`/`persist_run_snapshot` throughout.
- [x] T018 Persist completed and failed run snapshots in `logs/agent_runs/`. Confirmed - this is where the 10 run-state JSON files untracked from git this session (specs/012 hygiene pass) came from; the write path itself is correct and unaffected.
- [x] T019 Update the Agent tab to render completed and failed final_state data. `app/GUI/tabs/agent.py` renders `final_state` metrics for `completed`/`failed` status.
- [x] T020 Add UI refresh logic that does not rely only on in-memory session state. File-backed snapshots (`logs/agent_runs/`) + `st.rerun()`, not memory-only.
- [x] T021 Surface blackboard counts and run status in the status bar. `app/GUI/components/status_bar.py` shows target/findings counts via `get_blackboard_summary()`.

## Phase 4: Hardening

- [x] T022 Add JSON serialization safety for agent snapshots and blackboard writes. `json.dumps(..., default=str)` in both `contracts.py` and `blackboard.py`.
- [x] T023 Add schema/version checks for the blackboard initialization path. `_get_schema_version`/`_set_schema_version` in `memory_service.py`.
- [x] T024 Add dependency-failure handling for Ollama, WSL, and missing tools. `self_heal_node` + `should_continue()`'s dependency-error detection in `graph.py`.
- [x] T025 Limit self-heal behavior to genuine dependency failures only. Routing is string-scoped to `"not found"`/`"not installed"`/`"permission denied"`, not a catch-all.

## Phase 5: Validation

- [x] T026 Add a test that proves the RAG pipeline returns grounded local context. `tests/test_rag/test_rag_engine_threshold.py` (threshold filtering + context fusion).
- [x] T027 Add a test that proves the agent terminates after success or retry exhaustion. **Closed 2026-07-06**: `tests/test_modules/test_tactical_graph_termination.py` (7 tests) exercises `should_continue()` directly - exploit success, dependency-error retry routing, retry-budget exhaustion, missing-payload termination, and a config-driven (not hardcoded) retry bound.
- [x] T028 Add a test that proves the UI can display the final_state after completion. `tests/test_gui/test_dashboard.py` + `app/GUI/tabs/agent.py`'s final_state rendering path.
- [x] T029 Add a test that proves failed runs are not hidden as running. **Closed 2026-07-06**: extracted the stale-running reconciliation check in `app/GUI/tabs/agent.py` into a pure `_reconcile_agent_running_state()` function (behavior-preserving) and added `tests/test_gui/test_agent_tab_status.py` (5 tests) proving a `status=failed` (or `completed`) snapshot flips `agent_running` to `False` rather than continuing to display "Running".
- [x] T030 Run `py_compile` or equivalent syntax checks for edited Python modules. `python -m compileall -q app scripts tests` is the BLOCKING `build-validation` CI job.

## Out Of Scope For MVP

- [ ] T031 Add advanced multi-agent orchestration.
- [ ] T032 Add nonessential demo-only fallback behaviors to production runtime.
- [ ] T033 Add UI polish that does not change observability or correctness.
