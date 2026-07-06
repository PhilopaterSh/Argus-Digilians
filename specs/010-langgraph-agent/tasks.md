# Tasks: LangGraph Agent & LangChain RAG Architecture

**Input**: Updated plan from `/specs/010-langgraph-agent/plan.md`

**Goal**: deliver a reliable MVP first, then harden observability and resilience.

## Phase 0: Foundation Alignment

- [ ] T001 Define the canonical runtime entrypoints for the Streamlit dashboard and the agent runner.
- [ ] T002 Lock the `AgentState` schema to include durable messages, retry counters, and result fields.
- [ ] T003 Define the JSON shape for agent run events and final snapshots.
- [ ] T004 Document the production vs demo/test behavior split for fallbacks.

## Phase 1: RAG MVP

- [ ] T005 Implement document loading and structural chunk creation in `app/core/rag/document_processor.py` (canonical name per `012` §2.1).
- [ ] T006 Implement `RecursiveCharacterTextSplitter` as the plain/unknown-format **fallback** in `app/core/rag/document_processor.py` (structural chunking is primary).
- [ ] T007 Implement Ollama embeddings + FAISS indexing + `store/manifest.json` (one embedder per index, build-time fallback) in `app/core/rag/vector_store.py` (per `012` §3).
- [ ] T008 Implement the linear retrieval/query flow (with RAG-disabled degradation on embedder/dimension mismatch) in `app/core/rag/rag_engine.py`.
- [ ] T009 Add a smoke test script for retrieval and answer generation.

## Phase 2: Tactical Agent MVP

- [ ] T010 Implement the recon node without synthetic success data in `app/core/agent/nodes/recon.py`.
- [ ] T011 Implement the scanner node with real scan result ingestion in `app/core/agent/nodes/scanner.py`.
- [ ] T012 Implement the exploit node with explicit success/failure reporting in `app/core/agent/nodes/exploit.py`.
- [ ] T013 Implement the reflective node with real verification/context handling in `app/core/agent/nodes/reflective.py`.
- [ ] T014 Implement the post-exploit node to persist final results to the blackboard in `app/core/agent/nodes/post_exploit.py`.
- [ ] T015 Compile the LangGraph workflow in `app/core/agent/graph.py` with explicit termination rules and retry bounds.
- [ ] T016 Add a configurable `MAX_RETRIES` / recursion limit guard to the agent graph.

## Phase 3: Observability and UI

- [ ] T017 Write structured run events from the agent runner in `scripts/run_agent.py`.
- [ ] T018 Persist completed and failed run snapshots in `logs/agent_runs/`.
- [ ] T019 Update the Agent tab to render completed and failed final_state data.
- [ ] T020 Add UI refresh logic that does not rely only on in-memory session state.
- [ ] T021 Surface blackboard counts and run status in the status bar.

## Phase 4: Hardening

- [ ] T022 Add JSON serialization safety for agent snapshots and blackboard writes.
- [ ] T023 Add schema/version checks for the blackboard initialization path.
- [ ] T024 Add dependency-failure handling for Ollama, WSL, and missing tools.
- [ ] T025 Limit self-heal behavior to genuine dependency failures only.

## Phase 5: Validation

- [ ] T026 Add a test that proves the RAG pipeline returns grounded local context.
- [ ] T027 Add a test that proves the agent terminates after success or retry exhaustion.
- [ ] T028 Add a test that proves the UI can display the final_state after completion.
- [ ] T029 Add a test that proves failed runs are not hidden as running.
- [ ] T030 Run `py_compile` or equivalent syntax checks for edited Python modules.

## Out Of Scope For MVP

- [ ] T031 Add advanced multi-agent orchestration.
- [ ] T032 Add nonessential demo-only fallback behaviors to production runtime.
- [ ] T033 Add UI polish that does not change observability or correctness.
