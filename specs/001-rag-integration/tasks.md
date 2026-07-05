# Tasks: RAG System Integration

**Input**: Spec at `specs/001-rag-integration/spec.md`

**Organization**: Tasks grouped by implementation phase. All tasks completed as of 2026-06-27.

---

## Phase 1: Core RAG Module

**Purpose**: Build the foundational RAG components (config, embeddings, chunking, vector store, engine).

- [x] T001 Create `app/core/rag/` package structure with `__init__.py`
- [x] T002 Implement `RAGConfig` dataclass in `app/core/rag/config.py`
- [x] T003 Implement `EmbeddingFactory` in `app/core/rag/embeddings.py` — Ollama primary, HuggingFace fallback, OpenAI final fallback
- [x] T004 Implement `DocumentProcessor` in `app/core/rag/document_processor.py` — structural chunking for MD, JSON, CSV, PDF, TXT
- [x] T005 Implement `VectorStore` in `app/core/rag/vector_store.py` — FAISS build, load, search, persist
- [x] T006 Implement `RAGEngine` in `app/core/rag/rag_engine.py` — query, retrieve, augment, format_combined_context, add_document, rebuild_index

---

## Phase 2: Knowledge Base & Configuration

**Purpose**: Create seed documents and wire RAG config into the framework.

- [x] T007 Create `knowledge_base/` directory with `.gitkeep`
- [x] T008 Write seed document `knowledge_base/argus_security_knowledge.md` describing full Argus architecture
- [x] T009 Add `rag:` settings block to `config.yaml` (enabled, embedding_model, chunk_size, retriever_k, auto_rebuild)

---

## Phase 3: Brain Integration

**Purpose**: Connect RAG to ArgusBrain for context-aware LLM queries.

- [x] T010 Update `app/core/brain.py` — add `_refresh_blackboard()` to pull live SQLite state
- [x] T011 Update `app/core/brain.py` — add `_enrich_with_rag()` to retrieve and format static knowledge
- [x] T012 Update `app/core/brain.py` — modify `ask()` to call blackboard refresh + RAG enrichment before LLM
- [x] T013 Update `app/core/brain_v2.py` (Argus branch only) with same RAG + Blackboard fusion logic

---

## Phase 4: Documentation

**Purpose**: Document architecture, design decisions, and provide README.

- [x] T014 Create `app/core/rag/README.md` explaining RAG purpose, architecture, embedding model, chunking, and usage
- [x] T015 Update `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` — add 6 Mermaid diagrams (System Context, Component, Chunking Flow, Query Lifecycle, Index Build, Context Fusion)
- [x] T016 Rename old `docs/ARGUS_TECHNICAL_ARCHITECTURE.md` to `docs/ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md` for archival
- [x] T017 Create `specs/001-rag-integration/` speckit documentation (spec, plan, research, data-model, quickstart, tasks)

---

## Phase 5: Sync & Deploy

**Purpose**: Ensure identical deployment across both branches and push to GitHub.

- [x] T018 Copy all RAG changes to `remote_Argus_PhilopaterSh` branch
- [x] T019 Verify identical hashes for all RAG files across both directories
- [x] T020 Push `fix/copy-setup-to-scripts` branch to GitHub (commit 5631cfa, 11 files, 1365 insertions)

---

## Completion Summary

| Metric | Value |
|--------|-------|
| Files created/modified | 11 (RAG module: 6, brain: 2, config: 1, knowledge: 2, docs: 2) |
| Lines of code added | ~1365 |
| RAG module files | 6 Python files (init, config, embeddings, document_processor, vector_store, rag_engine) |
| Embedding fallback tiers | 3 (Ollama → HuggingFace → OpenAI) |
| Document formats supported | 5 (MD, JSON, CSV, PDF, TXT+YAML+HTML) |
| Branches deployed | 2 (Argus, remote_Argus_PhilopaterSh) |
