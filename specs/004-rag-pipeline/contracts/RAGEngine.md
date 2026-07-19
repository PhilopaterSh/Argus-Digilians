# Contract: RAGEngine

**Module**: `app/core/rag/rag_engine.py`

---

## Interface

```python
class RAGEngine:
    def __init__(self, config: Optional[RAGConfig] = None, model_name: Optional[str] = None): ...
    def initialize(self, rebuild: Optional[bool] = None) -> None: ...
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]: ...
    def retrieve_with_scores(self, query: str, k: Optional[int] = None) -> List[tuple]: ...
    def augment(self, query: str, context_chunks: List[str]) -> str: ...
    def query(self, query: str, k: Optional[int] = None) -> RAGResult: ...
    def query_relevant(self, query: str, k: Optional[int] = None) -> str: ...
    def add_document(self, file_path: str) -> bool: ...
    def rebuild_index(self) -> None: ...
    def format_context(self, query: str, k: Optional[int] = None) -> str: ...
    def format_combined_context(self, query: str, blackboard_context: str = "", k: Optional[int] = None) -> str: ...
```

## Behaviour

| Condition | Result |
|-----------|--------|
| `__init__` with no LLM | Lazy — does NOT call `EmbeddingFactory.get_embeddings()`; waits for `initialize()` |
| `initialize()` with auto_rebuild=True | Checks index; rebuilds if stale/missing |
| `initialize()` with auto_rebuild=False | Loads existing index; no rebuild |
| `query()` with empty KB | Returns `RAGResult(answer="No relevant information found...")` |
| `query()` with results below threshold | Returns same empty result |
| `add_document()` on new file | Chunks with DocumentProcessor splitter, adds to FAISS |
| `format_combined_context()` with both RAG + Blackboard | Returns concatenated context with labelled sections |

## RAGResult Fields

```python
@dataclass
class RAGResult:
    answer: str           # LLM-augmented answer (or raw context if no LLM)
    sources: List[dict]   # Filtered sources (score >= threshold)
    chunks: List[str]     # Content of filtered sources
    all_chunks: List[str] # All retrieved chunks before filtering
```

## Test Contract

- Test `initialize()` with all state combinations (loaded, stale, empty)
- Test `query()` returns correct RAGResult structure
- Test `augment()` returns context when no LLM available
- Test `add_document()` chunking consistency
- Test `format_combined_context()` formatting
- Test edge: no knowledge_base dir
