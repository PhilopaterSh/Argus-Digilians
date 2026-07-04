# Implementation Plan: RAG System Integration

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-27 | **Spec**: `specs/001-rag-integration/spec.md`

---

## Summary

Integrate a production-ready RAG system into the Argus AI penetration testing framework. The system uses nomic-embed-text (via Ollama) for embeddings, FAISS for vector storage, format-aware structural chunking for document processing, and a context fusion layer that merges static knowledge with live Blackboard state before sending prompts to the LLM.

---

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: langchain-ollama, langchain-huggingface, langchain-openai, faiss-cpu (or faiss-gpu), langchain-community, PyPDF2, pandas

**Storage**: FAISS vector index (local files at `app/core/rag/store/`), SQLite Blackboard (`argus_intelligence.db`)

**Testing**: pytest with mock embedding models and FAISS fixtures

**Target Platform**: Windows with WSL/Kali Linux backend

**Project Type**: CLI tool with AI agent orchestration

## Constitution Check

*GATE: Passed — no violations.*

---

## Project Structure

### Documentation (this feature)

```
specs/001-rag-integration/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Research findings
├── data-model.md        # Data model documentation
├── quickstart.md        # Quickstart guide
└── tasks.md             # Task breakdown
```

### Source Code

```
Argus/
├── app/core/rag/
│   ├── __init__.py              # Module exports
│   ├── config.py                # RAGConfig dataclass
│   ├── embeddings.py            # EmbeddingFactory (Ollama → HF → OpenAI)
│   ├── document_processor.py    # Structural chunker per format
│   ├── vector_store.py          # FAISS wrapper (build, load, search, persist)
│   ├── rag_engine.py            # RAGEngine (query, retrieve, augment, format)
│   └── store/                   # Persisted FAISS index files
│
├── app/core/brain.py            # ArgusBrain — _enrich_with_rag(), _refresh_blackboard()
├── app/core/brain_v2.py         # ArgusBrainV2 — same fusion logic
├── knowledge_base/              # Source documents for RAG ingestion
│   ├── .gitkeep
│   └── argus_security_knowledge.md
│
├── config.yaml                  # RAG settings block
└── docs/
    ├── ARGUS_FRAMEWORK_ARCHITECTURE_v2.md    # Updated with RAG + 6 diagrams
    └── ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md  # Pre-RAG archive
```

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| 3-tier embedding fallback chain | Ensures operation in offline/air-gapped environments | Single model would fail if unavailable |
| Structural vs fixed-size chunking | Different document formats carry meaning in structure | Fixed-size splits headers/rows/pages, losing semantic boundaries |

---

## Key Design Decisions

1. **nomic-embed-text over all-MiniLM-L6-v2**: Local execution via Ollama (no API key, no data leakage), 768-dim embeddings.
2. **RAG + Blackboard fusion**: Separate static knowledge from live target state to prevent hallucination. Prompt instructions prioritize live data.
3. **Structural chunking**: JSON → RecursiveJsonSplitter/array items, CSV → row-by-row, Markdown → MarkdownHeaderTextSplitter, PDF → PyPDFLoader, other → RecursiveCharacterTextSplitter (600 chunk, 100 overlap).
4. **Auto-rebuild**: FAISS index checks `knowledge_base/` modification time and rebuilds lazily on first query after change.
5. **Non-blocking design**: RAG failures never crash the query — fall back to Blackboard-only or raw LLM.
