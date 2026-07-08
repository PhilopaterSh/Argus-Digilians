# Feature Specification: LangGraph Agent & LangChain RAG Architecture

**Feature Branch**: `010-langgraph-agent`

**Created**: 2026-06-30

**Status**: Draft — **RAG architecture remains canonical** (per `012-spec-reconciliation` §4). The
**tactical-agent design (recon -> scanner -> exploit -> reflective, `app/core/agent/graph.py`)
is superseded as the production driver by `017-restore-react-agent`** (2026-07-08): investigation
found the project's originally-intended operating model (`app/core/prompts.py` + `ArgusBrain`'s
free-form ReAct tool selection) was fully built but wired only to deprecated GUI shims, while the
canonical `app/GUI/dashboard.py` ran this deterministic graph instead. `017` restores `ArgusBrain`
as the "Start Agent" driver; this graph's code remains in `app/core/agent/graph.py`/`nodes/` (not
deleted, per the Governance rule below) and its own tests stay green, but it is no longer invoked
by the production entrypoint (`scripts/run_agent.py`). Module names align to `012` §2.1/§2.2: RAG
uses `document_processor.py` / `vector_store.py` / `rag_engine.py` (not `processor/vectorstore/engine`);
agent code lives in `app/core/agent/`. Chunking is structural (canonical), with
`RecursiveCharacterTextSplitter` as the plain/unknown-format fallback. Embedding follows the
manifest design (`012` §3).

**Input**: User description: "Architecture split: LangChain for RAG (deterministic, linear), LangGraph for Tactical PenTest Agent (stateful, cyclical feedback loops)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - RAG Query Execution (Priority: P1)

As a system, I need to execute deterministic, linear Retrieval-Augmented Generation operations to answer user queries based on indexed files, so that I can provide accurate context without complex feedback loops.

**Why this priority**: RAG provides the foundational knowledge retrieval capability required for the system to understand the environment and context before acting.

**Independent Test**: Can be tested by loading a sample document into FAISS, querying it, and verifying the LLM receives the correct chunks.

**Acceptance Scenarios**:

1. **Given** a parsed document, **When** a user queries a topic, **Then** the system uses LangChain (FAISS, RecursiveCharacterTextSplitter, OllamaEmbeddings) to retrieve relevant chunks and generate a response.
2. **Given** a simple query, **When** the RAG pipeline is invoked, **Then** it completes in a linear fashion without cyclical looping.

---

### User Story 2 - Tactical PenTest Agent Execution (Priority: P1)

As a penetration testing engine, I need to use a stateful, cyclical feedback loop (LangGraph) to execute tactical operations, so that I can react to defenses (e.g., WAF blocks) and iteratively modify my payloads until successful.

**Why this priority**: Tactical pentesting requires dynamic decision-making and state tracking, which is the core intelligence of the Argus system.

**Independent Test**: Can be tested by simulating a blocked payload and verifying the agent routes to the Reflective Node, modifies the payload, and re-attempts the exploit.

**Acceptance Scenarios**:

1. **Given** a target with a WAF, **When** the Exploit Node's initial payload is blocked, **Then** the Reflective Node detects the block and modifies the payload for bypass.
2. **Given** a modified payload, **When** it is sent to the target, **Then** the Exploit Node transitions to the Post-Exploit Node upon success and records the state in the SQLite Blackboard.

### Edge Cases

- What happens when the Reflective Node cannot find a bypass after maximum retries?
- How does the system handle FAISS indexing failures or empty RAG results?
- What happens when a cyclical loop in LangGraph exceeds a safe execution threshold (infinite loop prevention)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use LangChain for all linear RAG operations (document splitting, embedding, retrieval) under `app/core/rag/`.
- **FR-002**: System MUST use LangGraph to orchestrate stateful tactical agents under `app/core/agent/`.
- **FR-003**: System MUST define distinct LangGraph nodes for: Recon, Scanner, Exploit, Reflective (Verification/Modification), and Post-Exploit.
- **FR-004**: System MUST maintain the pentest state across nodes using a LangGraph `StateGraph`.
- **FR-005**: System MUST persist the outcomes and extracted data to the SQLite Blackboard database upon successful post-exploitation.

### Key Entities

- **RAG Pipeline**: LangChain components (Document, Chunk, Embedding, FAISS Index).
- **Agent State**: LangGraph state dictionary (current_target, payloads_tried, exploit_status, extracted_data).
- **Node**: A functional step in the LangGraph (e.g., Recon Node, Exploit Node).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: RAG pipeline processes documents and answers queries with zero cyclical state management logic (purely linear).
- **SC-002**: PenTest Agent can successfully traverse a loop (Exploit -> Reflective -> Exploit) and break out upon success or max retries.
- **SC-003**: Agent state is accurately recorded in the SQLite Blackboard at the end of the graph execution.

## Assumptions

- Ollama is running and accessible for both embeddings and LLM reasoning.
- The SQLite Blackboard database schema is already capable of storing findings and global state.
- Target environments (for testing) are available to validate cyclical exploit logic.
