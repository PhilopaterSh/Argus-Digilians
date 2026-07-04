# Quickstart: RAG System

## Prerequisites

- Ollama installed with nomic-embed-text model: `ollama pull nomic-embed-text`
- Python 3.10+ with dependencies listed in `Setup/requirements.txt`

## Adding Knowledge

Drop files into `knowledge_base/`:

Supports: `.md`, `.json`, `.csv`, `.pdf`, `.txt`, `.yaml`, `.html`

The system automatically detects format and applies structural chunking.

## Configuration

Edit `config.yaml`:

```yaml
rag:
  enabled: true
  embedding_model: "nomic-embed-text"
  chunk_size: 600
  chunk_overlap: 100
  retriever_k: 4
  auto_rebuild: true
```

## Verification

Run a test query via ArgusBrain:

```python
from app.core.rag.rag_engine import RAGEngine
engine = RAGEngine()
result = engine.query("How to detect SQL injection?")
print(result["response"])
```

Or simply ask the AI through the normal CLI and check if responses include knowledge base content.

## Architecture Files

| File | Purpose |
|------|---------|
| `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` | Full architecture with 6 Mermaid diagrams |
| `app/core/rag/README.md` | Detailed RAG-specific documentation |
| `app/core/rag/embeddings.py` | Embedding model selection |
| `app/core/rag/document_processor.py` | Document chunking logic |
| `app/core/rag/vector_store.py` | FAISS index management |
| `app/core/rag/rag_engine.py` | Query and context fusion |
