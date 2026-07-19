# Contract: EmbeddingFactory

**Module**: `app/core/rag/embeddings.py`

---

## Interface

```python
class EmbeddingFactory:
    @classmethod
    def get_embeddings(cls, config: Optional[RAGConfig] = None) -> Embeddings: ...
    @classmethod
    def reset(cls) -> None: ...
```

## Behaviour

| Condition | Result |
|-----------|--------|
| Ollama available on localhost:11434 | Returns `OllamaEmbeddings(model=config.embedding_model)` |
| Ollama fails, HuggingFace available | Returns `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")` |
| Both fail, OpenAI key set | Returns `OpenAIEmbeddings(model="text-embedding-3-small")` |
| All 3 tiers fail | Raises `ImportError` |
| `reset()` called | Clears cached embedding model; next `get_embeddings()` re-evaluates |

## Test Contract

- Each tier must be mockable independently via dependency injection
- `reset()` must invalidate cached singleton
- No network calls in unit tests — use `unittest.mock.patch`
