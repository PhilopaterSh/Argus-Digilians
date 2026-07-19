# Quickstart: Validating the RAG Pipeline

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Prerequisites

- Python 3.12+ with `Argus_venv` activated
- At least one document in `knowledge_base/`
- (Optional) Ollama running with `nomic-embed-text` for full integration tests

## Validation Steps

### 1. Unit Tests

```bash
cd <project-root>
.\Argus_venv\Scripts\Activate.ps1
pytest tests/test_rag/ -v
```

Expected: 15+ tests passing, covering:
- Embedding fallback chain (3 tiers → mocked)
- Document loading + splitting (txt, md, pdf, csv, json)
- FAISS checksum verification
- RAGEngine query flow
- Edge cases: empty KB, binary files, missing index

### 2. Integration Test (manual)

```python
from app.core.rag import RAGEngine

engine = RAGEngine()
result = engine.query("What is port scanning?")
print(result.answer)
```

Expected: Returns answer from knowledge base or "No relevant information found."

### 3. Fallback Test

```bash
# Stop Ollama
.\Argus_venv\Scripts\Activate.ps1
python -c "from app.core.rag import RAGEngine; e=RAGEngine(); print(e.retrieve('test'))"
```

Expected: Falls back to HuggingFace (all-MiniLM-L6-v2) without crashing.

### 4. FAISS Integrity Test

```bash
python -c "
from app.core.rag import RAGEngine
e = RAGEngine()
# Touch a file to change mtime
import pathlib; pathlib.Path('knowledge_base/.gitkeep').touch()
print(e.retrieve('test'))  # Should trigger rebuild
"
```

Expected: Index rebuilt automatically when KB changes detected.
