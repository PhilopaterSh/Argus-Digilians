# Implementation Plan: LangGraph Agent & LangChain RAG Architecture

**Branch**: `010-langgraph-agent` | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-langgraph-agent/spec.md`

## Summary

This feature should ship as two clearly separated subsystems:

- A deterministic, linear RAG pipeline for local knowledge retrieval.
- A stateful tactical agent built with LangGraph for controlled multi-step execution.

The priority is a reliable MVP with truthful state reporting, explicit loop bounds, and observable execution. Runtime logic must not fabricate results. Any simulation or fallback behavior belongs only in tests or dedicated demo mode, never in the main execution path.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: LangChain, LangGraph, FAISS, Ollama

**Storage**: SQLite Blackboard database, FAISS vector store, JSON event/state logs

**Testing**: pytest plus standalone smoke scripts

**Target Platform**: Windows host with local Ollama; WSL/Kali bridge for tactical tooling

**Project Type**: Local agentic backend with Streamlit dashboard

**Performance Goals**:
- RAG retrieval should remain sub-second for typical local corpora.
- Agent execution should expose progress and terminate deterministically on success, failure, or retry budget exhaustion.

**Constraints**:
- Offline-capable local execution is the default.
- No external LLM API calls in the normal path.
- The UI must read the same durable state that the agent writes.

## Constitution Check

- **I. Admin-First Elevation**: Not applicable to the AI layer.
- **II. Single-Source Installer**: Not applicable.
- **III. Idempotent & Test-Gated**: Required for agent state, logs, and blackboard writes.
- **IV. Platform-Boundary Clarity**: Required. Windows UI, local Ollama, and WSL/Kali tooling must remain separated.
- **V. Observability & Logging**: Required. Every node must emit structured events and the UI must surface them.
- **VI. English-Only Documentation**: Required. All spec text and code comments added here must remain in English.

## Architecture Principles

1. Keep RAG linear and deterministic.
2. Keep tactical execution stateful and bounded.
3. Never invent results in runtime code.
4. Treat logs and state files as first-class output artifacts.
5. Prefer real tool/service integration over heuristic stand-ins.
6. Keep demo or simulation flows isolated from production flows.

## Project Structure

### Documentation

```text
specs/010-langgraph-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
└── spec.md
```

### Source Code

```text
# Canonical names per 012 §2.1/§2.2 (RAG uses descriptive names; agent in app/core/agent/)
app/
├── core/
│   ├── rag/
│   │   ├── config.py              # RAGConfig
│   │   ├── embeddings.py          # EmbeddingFactory (build-time fallback; manifest per 012 §3)
│   │   ├── document_processor.py  # structural chunking (RecursiveCharacterTextSplitter = fallback)
│   │   ├── vector_store.py        # FAISS + store/manifest.json
│   │   └── rag_engine.py          # linear retrieval + context fusion
│   └── agent/
│       ├── brain.py               # single ArgusBrain (reasoning + registry dispatch) — 012 §2.2
│       ├── agent_factory.py       # create_default_registry/create_brain/register_all_tools
│       ├── state.py               # AgentState
│       ├── nodes/
│       │   ├── recon.py
│       │   ├── scanner.py
│       │   ├── exploit.py
│       │   ├── reflective.py
│       │   └── post_exploit.py
│       └── graph.py               # canonical LangGraph builder (+ parser/hooks migrated from 013)
├── GUI/
│   ├── dashboard.py               # unified Argus Studio (011); LAUNCH_STUDIO.bat → port 12199
│   ├── tabs/
│   └── utils/
└── tools/
    ├── recon.py
    ├── self_heal.py
    └── tool_registry.py           # WSLBridgeTools facade over ToolRegistry (17 tools)
```

## Delivery Plan

### Phase 0: Foundation Alignment

Goal: make the contracts between RAG, Agent, UI, and storage explicit before expanding behavior.

- Lock the agent state schema.
- Define durable event/state log format.
- Decide the canonical entrypoints.
- Confirm the UI reads the same state file the runner writes.

### Phase 1: RAG MVP

Goal: build a deterministic local retrieval pipeline.

- Load local documents.
- Split documents with `RecursiveCharacterTextSplitter`.
- Create embeddings through Ollama.
- Index vectors in FAISS.
- Retrieve context and answer with a linear flow.
- Add smoke tests that confirm retrieval quality and failure handling.

### Phase 2: Tactical Agent MVP

Goal: build a bounded LangGraph workflow that can execute, retry, and exit cleanly.

- Implement recon, scanner, exploit, reflective, and post-exploit nodes.
- Wire explicit transitions and termination conditions.
- Set a configurable retry ceiling.
- Persist outcomes to the SQLite Blackboard.
- Make the recon path truthful: no synthetic open ports in runtime.

### Phase 3: Observability and UI

Goal: make progress, completion, and failure visible in real time.

- Emit a structured event for every node transition.
- Persist snapshots for completed and failed runs.
- Render running, completed, and failed states in the dashboard.
- Show final_state summaries directly in the UI.
- Add auto-refresh only if it does not obscure the actual state source.

### Phase 4: Hardening

Goal: remove fragile assumptions and make the runtime resilient.

- Add state serialization safety.
- Add schema/version checks for the blackboard.
- Add dependency-failure handling.
- Keep self-heal limited to genuine missing-tool cases.
- Separate test/demo fallbacks from production execution.

### Phase 5: Validation

Goal: prove both subsystems independently and together.

- Verify RAG returns relevant local context.
- Verify agent loops terminate at the retry ceiling.
- Verify final results render after completion.
- Verify failed runs are visible and not hidden behind running state.

## Risks And Mitigations

- **Risk**: Fallbacks hide real failures.
  - **Mitigation**: Do not use fabricated results in runtime; log failure explicitly.
- **Risk**: The UI shows stale running state.
  - **Mitigation**: Read the durable run state on each render and expose final_state.
- **Risk**: Infinite or excessive agent loops.
  - **Mitigation**: Enforce max retries and a recursion/execution limit.
- **Risk**: Ollama or WSL/Kali dependencies are unavailable.
  - **Mitigation**: Fail clearly and surface dependency status in the dashboard.

## Success Criteria

- RAG runs linearly and produces grounded answers from local indexed content.
- Agent state is durable, observable, and bounded.
- UI displays live progress and final results truthfully.
- No runtime stub pretends a scan or exploit succeeded.
- Blackboard records completed runs with consistent snapshots.
