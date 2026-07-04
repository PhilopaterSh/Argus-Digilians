# Data Model: RAG System

---

## RAGConfig

Configuration loaded from `config.yaml` `rag:` section.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| enabled | bool | true | Enable/disable RAG enrichment |
| embedding_model | str | "nomic-embed-text" | Ollama model name |
| embedding_device | str | "cpu" | Device for embeddings |
| chunk_size | int | 600 | Max chars per chunk (fixed-size only) |
| chunk_overlap | int | 100 | Overlap between chunks |
| retriever_k | int | 4 | Number of chunks to retrieve |
| similarity_threshold | float | 0.5 | Minimum similarity score |
| auto_rebuild | bool | true | Auto-rebuild index on changes |
| knowledge_base_dir | str | "knowledge_base" | Path to source documents |

---

## DocumentChunk

Produced by `DocumentProcessor`, stored in FAISS index.

| Field | Type | Description |
|-------|------|-------------|
| page_content | str | The chunk text |
| metadata | dict | Source file, chunk type (header/row/page), position |
| embedding | List[float] | Vector embedding (768-dim for nomic) |

---

## FAISS Index

Persisted to disk at `app/core/rag/store/`.

| File | Description |
|------|-------------|
| index.faiss | FAISS vector index (binary) |
| index.pkl | Accompanying metadata pickle |

---

## BlackboardContext

Live state from SQLite via `memory_service.py`.

| Source | Method | Returns |
|--------|--------|---------|
| Targets + Findings | get_blackboard_summary() | Dict of target IPs, open ports, discovered technologies, findings |
| Entities + Relations | get_graph_insights() | Knowledge graph edges (entity --[relation]--> entity) |

---

## FusedPrompt

The final prompt structure sent to Ollama LLM:

```
===== STATIC KNOWLEDGE BASE (techniques, cheatsheets) =====
[chunk 1 text]
[chunk 2 text]
...

===== LIVE TARGET STATE (active reconnaissance findings) =====
[Blackboard Intelligence]
[summary of current target state]

[Knowledge Graph Relations]
[entity relationships]

===== USER QUERY =====
[user question]
```

**Priority instruction**: "If the live target state contradicts the static knowledge base, trust the live target state."
