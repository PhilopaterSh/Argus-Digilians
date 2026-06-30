# Implementation Plan: LangGraph Agent & LangChain RAG Architecture

**Branch**: `010-langgraph-agent` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-langgraph-agent/spec.md`

## Summary

This plan solidifies the architectural decision to strictly separate the deterministic RAG pipeline (using LangChain) from the stateful, cyclical Tactical PenTest Agent (using LangGraph). The RAG subsystem handles linear document processing and querying, while the Agent orchestrates reconnaissance, scanning, and exploitation with built-in feedback loops for evasion and bypass, storing results in the SQLite Blackboard.

## Technical Context

**Language/Version**: Python 3.12 (standardized across Argus)

**Primary Dependencies**: LangChain, LangGraph, FAISS, Ollama

**Storage**: SQLite (Blackboard database), FAISS (Vector store)

**Testing**: pytest

**Target Platform**: Windows host + Kali Linux WSL2 guest

**Project Type**: Agentic CLI / Backend Architecture

**Performance Goals**: Low latency vector retrieval (<1s), stable graph state transitions

**Constraints**: Must operate entirely local (offline-capable) using Ollama; no external LLM API calls.

**Scale/Scope**: Sub-components of the core Argus engine under `app/core/rag/` and `app/core/agent/`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Admin-First Elevation**: N/A for core AI logic.
- **II. Single-Source Installer**: N/A.
- **III. Idempotent & Test-Gated**: N/A for install, but LangGraph ensures state is safely managed.
- **IV. Platform-Boundary Clarity**: The agent runs in Python on Windows but orchestrates tools via the WSL bridge (SSH). This architecture respects the boundary.
- **V. Observability & Logging**: LangGraph state updates provide built-in observability into the agent's thought process.
- **VI. English-Only Documentation**: Verified. All specs, plans, and docstrings will be in English.

## Project Structure

### Documentation (this feature)

```text
specs/010-langgraph-agent/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
app/
├── core/
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── processor.py     # LangChain document loaders & splitters
│   │   ├── vectorstore.py   # FAISS integration
│   │   └── engine.py        # Linear RAG querying flow
│   └── agent/
│       ├── __init__.py
│       ├── state.py         # LangGraph StateGraph definitions
│       ├── nodes/
│       │   ├── recon.py
│       │   ├── scanner.py
│       │   ├── exploit.py
│       │   ├── reflective.py
│       │   └── post_exploit.py
│       └── graph.py         # LangGraph compilation & workflow logic
```

**Structure Decision**: The logic is split cleanly into `app/core/rag` for LangChain and `app/core/agent` for LangGraph, establishing strict boundaries between linear and cyclical components.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. The dual-framework approach prevents "spaghetti code" by applying the right tool (LangChain vs LangGraph) to the right problem domain.
