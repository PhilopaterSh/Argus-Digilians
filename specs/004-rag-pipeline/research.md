# Research: RAG Pipeline Audit & Hardening

**Phase**: 0 — Technical Research | **Date**: 2026-06-29

---

## Current State Analysis

### Files Audited

| Module | LOC | Tests | Issues Found |
|--------|-----|-------|-------------|
| `config.py` | 36 | None | ✅ Clean, minor: `from_dict` could skip unknown keys silently |
| `embeddings.py` | 78 | None | ⚠️ Singleton pattern; no reset mechanism; no caching fallback |
| `document_processor.py` | 156 | None | ⚠️ Dead import (`io`); no protection against binary/unreadable files |
| `vector_store.py` | 109 | None | ⚠️ No checksum/hash; `allow_dangerous_deserialization=True` always; no context manager |
| `rag_engine.py` | 184 | None | ⚠️ Eager init in `__init__`; no lazy embedding loading |
| `__init__.py` | 13 | None | ✅ Clean |

**Total**: ~576 LOC across 6 modules | **Test coverage**: 0%

### Key Technical Issues

1. **No staleness detection** (`vector_store.py` line 45–70): `load_index()` always loads existing index without verifying if the knowledge base has changed since last build.
2. **Eager embedding init** (`rag_engine.py` line 59): `EmbeddingFactory.get_embeddings()` is called in `__init__`, meaning RAGEngine cannot be instantiated without a working embedding model. Should be lazy.
3. **Dead import** (`document_processor.py` line 4): `import io` is never used.
4. **Missing structured logging**: All modules use bare `print()` — violates Constitution §V.
5. **Chunking gap**: `add_document()` (rag_engine.py:139–143) uses a fresh `RecursiveCharacterTextSplitter` instead of the processor's structural splitter, producing inconsistent chunking.
6. **No `__len__` or context manager**: Unlike `memory_service.py` (Phase 003), `VectorStore` lacks Pythonic protocols.

## Embedding Fallback Analysis

The 3-tier fallback in `embeddings.py` is correct in logic but untestable because:
- `_try_ollama` connects to a real `localhost:11434` — cannot mock without refactoring
- `_try_huggingface` downloads model weights — heavy for CI
- `_try_openai` requires env `OPENAI_API_KEY`

**Recommendation**: Accept embedding model as a constructor parameter so tests inject a dummy embedder.

## FAISS Index Strategy

- **Current**: FAISS index saved at `app/core/rag/store/index.faiss` with metadata pickle
- **Problem**: `allow_dangerous_deserialization=True` is passed unconditionally; no checksum file exists
- **Fix**: Write a `.checksum` file alongside the index; verify before loading; warn if checksum mismatch

## Dependencies Required

All already present in `Argus_venv` (via `requirements_embedded.txt`):
- `langchain-core`, `langchain-community`, `langchain-ollama`, `langchain-huggingface`, `langchain-openai`
- `faiss-cpu`
- `sentence-transformers`
- `pypdf`

## Recommended Approach

1. Refactor `EmbeddingFactory` to accept a callable/lazy provider instead of real model init at class level
2. Add FAISS checksum (SHA256 of knowledge base directory listing)
3. Add structured logging via Python `logging` module
4. Add lazy init to `RAGEngine`
5. Fix `add_document()` chunking inconsistency
6. Remove dead imports
7. Write 4 test files covering all 6 modules
8. Add `__len__` and context manager support to `VectorStore`

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| HuggingFace download fails in CI | Medium | High | Use mock embeddings in tests |
| FAISS deserialization of untrusted index | Low (local) | Critical | Add checksum verification |
| Embedding fallback chain not tested | High | Medium | Mock each tier independently |
