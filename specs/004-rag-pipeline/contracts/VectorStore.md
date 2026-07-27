# Contract: VectorStore

**Module**: `app/core/rag/vector_store.py`

---

## Interface

```python
class VectorStore:
    def __init__(self, config: Optional[RAGConfig] = None): ...
    def build_index(self, chunks: List[Document]) -> int: ...
    def load_index(self) -> bool: ...
    def rebuild_from_directory(self, directory: Optional[str] = None) -> int: ...
    def similarity_search(self, query: str, k: Optional[int] = None) -> List[Document]: ...
    def similarity_search_with_score(self, query: str, k: Optional[int] = None) -> List[tuple]: ...
    def get_retriever(self, k: Optional[int] = None) -> VectorStoreRetriever: ...

    @property
    def is_loaded(self) -> bool: ...
    @property
    def index_size(self) -> int: ...
```

## Behaviour

| Condition | Result |
|-----------|--------|
| Index file exists + checksum valid | `load_index()` returns True, index loaded into memory |
| Index file exists + checksum invalid | `load_index()` returns False → triggers rebuild |
| No index file | `load_index()` returns False |
| `build_index([])` (empty chunks) | Returns 0, no action |
| Checksum file missing | Treated as invalid → triggers rebuild |
| `allow_dangerous_deserialization` | Only used if checksum passes |

## Persistence Layout

```
app/core/rag/store/
├── index.faiss       # FAISS serialized index
├── index.pkl         # FAISS docstore (auto-saved by FAISS.save_local)
└── .checksum         # SHA256 of KB file listing
```

## Test Contract

- Test `build_index` with 0, 1, and N chunks
- Test `load_index` with valid checksum, invalid checksum, no index
- Test `similarity_search` returns correct number of results
- Test `rebuild_from_directory` integration with DocumentProcessor
- Test `index_size` property
