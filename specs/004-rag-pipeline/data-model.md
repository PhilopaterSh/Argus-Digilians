# Data Model: RAG Pipeline

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Data Flow

```
User Query
    │
    ▼
RAGEngine.query()
    │
    ├── RAGEngine.initialize()
    │       ├── VectorStore.load_index()
    │       │       ├── Read index.faiss + metadata.pkl
    │       │       ├── Verify .checksum against knowledge_base/
    │       │       └── Return True/False
    │       │
    │       └── If load fails or auto_rebuild:
    │               VectorStore.rebuild_from_directory()
    │                   ├── DocumentProcessor.process_directory()
    │                   │       ├── load_from_directory() → raw Document[]
    │                   │       └── split_documents() → chunked Document[]
    │                   └── VectorStore.build_index()
    │                           ├── EmbeddingFactory.get_embeddings()
    │                           │       ├── _try_ollama() → OllamaEmbeddings
    │                           │       ├── _try_huggingface() → HuggingFaceEmbeddings
    │                           │       └── _try_openai() → OpenAIEmbeddings
    │                           └── FAISS.from_documents() → FAISS index
    │
    └── VectorStore.similarity_search_with_score()
            └── FAISS.similarity_search_with_score()
                    └── (Document, score)[]

RAGEngine.augment(query, chunks)
    └── RAG_PROMPT | build_llm() | StrOutputParser
            └── str (augmented answer)
```

## Entity Relationship

```
RAGConfig (dataclass)
    │
    ├── used by RAGEngine
    ├── used by EmbeddingFactory
    ├── used by DocumentProcessor
    └── used by VectorStore

EmbeddingFactory (singleton)
    └── get_embeddings() → Embeddings model (Ollama | HuggingFace | OpenAI)

DocumentProcessor
    ├── load_from_directory() → Document[]
    ├── load_file() → Document[] | None
    └── split_documents() → Document[] (chunked)

VectorStore
    ├── build_index(chunks) → int
    ├── load_index() → bool
    ├── rebuild_from_directory() → int
    ├── similarity_search(query) → Document[]
    ├── similarity_search_with_score(query) → (Document, score)[]
    └── get_retriever() → VectorStoreRetriever

RAGEngine
    ├── initialize()
    ├── retrieve(query) → Document[]
    ├── query(query) → RAGResult
    ├── query_relevant(query) → str
    ├── augment(query, chunks) → str
    ├── add_document(path) → bool
    ├── rebuild_index()
    ├── format_context(query) → str
    └── format_combined_context(query, blackboard) → str
```

## State Model

| State | Condition | Action |
|-------|-----------|--------|
| Uninitialized | `_initialized = False` | `initialize()` loads or builds index |
| Loaded | Index exists + checksum valid | `similarity_search()` runs |
| Stale | Index missing or checksum mismatch | `rebuild_from_directory()` |
| Empty | No knowledge_base/ or empty | Return empty results gracefully |

## Checksum Format

SHA256 hash of sorted file listing (relative paths + mtime):

```
# stored at: app/core/rag/store/.checksum
a1b2c3d4...  knowledge_base/argus_security_knowledge.md
e5f6g7h8...  knowledge_base/network_scanning_cheatsheet.md
```

Compare on load; if any entry changed, trigger rebuild.
