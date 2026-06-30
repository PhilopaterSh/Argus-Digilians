# Tasks: LangGraph Agent & LangChain RAG Architecture

**Input**: Design documents from `/specs/010-langgraph-agent/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create initial package structure: `app/core/rag/__init__.py` and `app/core/agent/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Verify Python dependencies (langchain, langgraph, faiss-cpu, sqlite3) in project environment.
- [X] T003 Setup Blackboard SQLite schema connection logic (for later use by Post-Exploit)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - RAG Query Execution (Priority: P1) 🎯 MVP

**Goal**: Execute deterministic, linear Retrieval-Augmented Generation operations to answer user queries based on indexed files without complex feedback loops.

**Independent Test**: Can be tested by loading a sample document into FAISS, querying it, and verifying the LLM receives the correct chunks.

### Implementation for User Story 1

- [X] T004 [P] [US1] Create RAG Document Chunk schema in `app/core/rag/processor.py`
- [X] T005 [US1] Implement LangChain text splitters and loaders in `app/core/rag/processor.py`
- [X] T006 [P] [US1] Implement FAISS vector store and OllamaEmbeddings integration in `app/core/rag/vectorstore.py`
- [X] T007 [US1] Implement linear RAG querying flow chain in `app/core/rag/engine.py` (depends on T005, T006)

**Checkpoint**: At this point, User Story 1 (RAG Engine) should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Tactical PenTest Agent Execution (Priority: P1)

**Goal**: Use a stateful, cyclical feedback loop (LangGraph) to execute tactical operations, react to defenses, and iteratively modify payloads.

**Independent Test**: Can be tested by simulating a blocked payload and verifying the agent routes to the Reflective Node and re-attempts the exploit.

### Implementation for User Story 2

- [X] T008 [P] [US2] Define Tactical Agent State (`TypedDict`) in `app/core/agent/state.py`
- [X] T009 [P] [US2] Implement Recon Node function in `app/core/agent/nodes/recon.py`
- [X] T010 [P] [US2] Implement Scanner Node function in `app/core/agent/nodes/scanner.py`
- [X] T011 [P] [US2] Implement Exploit Node function in `app/core/agent/nodes/exploit.py`
- [X] T012 [P] [US2] Implement Reflective Node (Verify/Modify) function in `app/core/agent/nodes/reflective.py`
- [X] T013 [P] [US2] Implement Post-Exploit Node function in `app/core/agent/nodes/post_exploit.py`
- [X] T014 [US2] Compile LangGraph workflow and state transitions in `app/core/agent/graph.py` (depends on T008-T013)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T015 [P] Create standalone test script `scripts/test_rag.py` to validate US1
- [X] T016 [P] Create standalone test script `scripts/test_agent.py` to validate US2
- [X] T017 Validate architectural rules are strictly followed (no loops in RAG, explicit state in Agent)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Both US1 and US2 are P1 priority and can run in parallel.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Node creation inside US2 (T009-T013) can run completely in parallel before graph compilation.
- Standalone test script creation (T015, T016) can run in parallel.

---

## Implementation Strategy

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (RAG) → Test independently → Validate linear flow
3. Add User Story 2 (Tactical Agent) → Test independently → Validate cyclical execution
4. Both architectures demonstrate their respective strengths side-by-side.
