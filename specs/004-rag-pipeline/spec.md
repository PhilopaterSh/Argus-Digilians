# Feature Specification: RAG Pipeline Audit & Hardening

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-29

**Status**: Draft

**Input**: The RAG subsystem was built in Phase 001 (`app/core/rag/`) but was never formally tested, has no unit tests, and the embedding fallback chain (Ollama → HuggingFace → OpenAI) has never been verified end-to-end. This feature hardens the RAG pipeline with tests, error handling, and proper FAISS index management.

---

## User Scenarios & Testing

### User Story 1 - Reliable RAG Queries (Priority: P1)

As a user, I want RAG-augmented queries to never crash due to a missing embedding model, so the AI always gets context even if Ollama is restarting.

**Independent Test**: Stop Ollama, run a RAG query — it should fall back to HuggingFace silently.

### User Story 2 - FAISS Index Integrity (Priority: P1)

As a developer, I want the FAISS index to be rebuilt automatically when the knowledge base changes, so stale data is never retrieved.

**Acceptance Scenarios**:
1. Given a new file in `knowledge_base/`, When RAGEngine loads, Then it should detect the change and trigger a rebuild.
2. Given a corrupted FAISS index, When RAGEngine loads, Then it should rebuild from scratch.

### User Story 3 - Test Coverage (Priority: P2)

As a developer, I want unit tests for all 6 RAG modules, so regressions are caught immediately.

---

## Requirements

- **FR-001**: Each embedding fallback tier MUST be tested (Ollama nomic-embed-text, HuggingFace all-MiniLM-L6-v2).
- **FR-002**: FAISS index MUST have a checksum/hash file to detect staleness.
- **FR-003**: RAGEngine MUST handle missing index gracefully (return empty context, not crash).
- **FR-004**: DocumentProcessor MUST handle binary/unreadable files without crashing.
- **FR-005**: All 6 RAG modules MUST have type hints and error handling.

## Key Entities

- `app/core/rag/` — 6 Python files (config.py, embeddings.py, document_processor.py, vector_store.py, rag_engine.py, __init__.py)
- `knowledge_base/` — seed documents for FAISS ingestion
- `app/core/rag/store/` — FAISS index persistence directory
