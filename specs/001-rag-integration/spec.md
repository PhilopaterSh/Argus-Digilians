# Feature Specification: RAG System Integration

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-27

**Status**: Implemented — **Refined By** `012-spec-reconciliation` §3 (embedding/index design) and §2.1 (canonical names). Where FR-005..007 below conflict with `012` §3, **`012` wins** (see the corrected wording inline). Python version: canonical **3.12** per `012` §2.6.

**Input**: Integrate Retrieval-Augmented Generation (RAG) into the Argus AI penetration testing framework, combining static security knowledge (FAISS vector store) with live target state (SQLite Blackboard) for context-aware AI decision-making.

---

## User Scenarios & Testing

### User Story 1 - Query with RAG Context (Priority: P1)

As a penetration tester, I want the AI to answer my questions using both its training data AND a local knowledge base of security techniques, so that responses are grounded in verified documentation.

**Why this priority**: Core value of RAG - every user interaction benefits from enriched context.

**Independent Test**: Can be tested by asking the AI a security question and verifying the response includes information from the knowledge base.

**Acceptance Scenarios**:

1. **Given** the RAG system is enabled and the knowledge base has documents, **When** a user asks a security-related question, **Then** the response should reference the retrieved knowledge.
2. **Given** the RAG system is enabled, **When** a user asks about a target's vulnerabilities, **Then** the response should include both static knowledge (techniques) and live Blackboard data (findings).

---

### User Story 2 - Knowledge Base Management (Priority: P2)

As a penetration tester, I want to add new security documents (Markdown, JSON, CSV, PDF) to the knowledge base and have them automatically indexed.

**Why this priority**: The value of RAG grows as the knowledge base expands.

**Independent Test**: Drop a file into `knowledge_base/` and verify it appears in search results.

**Acceptance Scenarios**:

1. **Given** a new Markdown file is added to `knowledge_base/`, **When** a query matches its content, **Then** the relevant section should be returned.
2. **Given** a CSV file with payload data, **When** a query matches a row, **Then** that row's content should be retrievable.

---

### User Story 3 - Offline Operation with Fallback (Priority: P3)

As a penetration tester in an isolated environment, I want the embedding model to work offline and gracefully fall back if the primary model is unavailable.

**Why this priority**: Critical for air-gapped pentest environments, but edge case.

**Independent Test**: Disconnect from the internet, stop Ollama, and verify the system falls back to HuggingFace embeddings without crashing.

**Acceptance Scenarios**:

1. **Given** Ollama is not running, **When** the RAG engine initializes, **Then** it should load HuggingFace embeddings as fallback.
2. **Given** no embedding model is available, **When** a query is made, **Then** the system should fall back to Blackboard-only or raw LLM query.

---

### Edge Cases

- What happens when `knowledge_base/` is empty? — RAG returns no static context, system works with Blackboard-only.
- What happens when FAISS index is corrupted? — Auto-rebuild triggers.
- What happens when the same document is updated? — Index is rebuilt and old chunks are replaced.
- How does the system handle very large documents? — Structural chunking splits by format (headers, rows, pages) to stay within 600-char chunks.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve relevant document chunks from FAISS based on cosine similarity to the query.
- **FR-002**: System MUST support Markdown (header-based), JSON (item/recursive), CSV (row-based), PDF (page-based), and plain text (fixed-size) chunking.
- **FR-003**: System MUST merge static knowledge (FAISS) with live target state (SQLite Blackboard) in the prompt.
- **FR-004**: System MUST prioritize live state over static knowledge when they contradict.
- **FR-005**: System MUST use nomic-embed-text via Ollama (768-dim) as the primary embedding model, and MUST persist the chosen embedder in `app/core/rag/store/manifest.json` (name, provider, dimension, knowledge_base hash, built_at, schema_version). *(Refined per `012` §3, FR-C1.)*
- **FR-006**: The embedder fallback chain (Ollama → HuggingFace all-MiniLM-L6-v2 → OpenAI text-embedding-3-small) applies **only at build/rebuild time** to pick an available embedder; the selected embedder is pinned in the manifest. Silent *query-time* substitution across different dimensions is FORBIDDEN. *(Refined per `012` §3, FR-C2 — this replaces the previous query-time fallback wording.)*
- **FR-007**: If the manifest's embedder is unavailable at query time and no rebuild is possible, System MUST degrade to Blackboard-only / raw-LLM (RAG-disabled) rather than query a dimension-mismatched index — preserving the non-blocking guarantee (FR-010) without a dimension error. *(Refined per `012` §3, FR-C4.)*
- **FR-008**: System MUST rebuild the FAISS index deterministically when either the `knowledge_base/` content hash OR the configured embedder differs from `manifest.json` (replaces the previous mtime-only heuristic). *(Refined per `012` §3, FR-C3; `manifest.json` also serves the integrity role in `004`.)*
- **FR-009**: System MUST accept configuration via `config.yaml` (enabled, model, chunk_size, retriever_k).
- **FR-010**: System MUST NOT block the query if RAG fails — fall back to Blackboard-only or raw LLM.

### Key Entities

- **DocumentChunk**: A segment of a source document with text content, metadata (source file, page/row/header), and an embedding vector.
- **FAISS Index**: A persisted vector store at `app/core/rag/store/` containing all embedded chunks.
- **EmbeddingModel**: An abstraction over Ollama/HuggingFace/OpenAI that produces vector embeddings for text.
- **BlackboardContext**: Live target state from SQLite including findings, entities, and relationships.
- **FusedPrompt**: The final prompt combining static knowledge + live state + user query, sent to the LLM.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Retrieval returns top-k (default 4) chunks with similarity scores within 500ms.
- **SC-002**: Index rebuild completes within 30 seconds for a knowledge base of 50 documents.
- **SC-003**: System does not crash if Ollama is unavailable — falls back gracefully.
- **SC-004**: Fused prompt clearly separates "STATIC KNOWLEDGE BASE" from "LIVE TARGET STATE" sections.

---

## Assumptions

- Ollama is installed and serves nomic-embed-text on localhost:11434.
- The knowledge base directory is `knowledge_base/` at the project root.
- The FAISS store is persisted at `app/core/rag/store/`.
- RAG is an enhancement layer — Argus functions without it (Blackboard + raw LLM).
- Structural chunking preserves meaning better than fixed-size for known formats.
