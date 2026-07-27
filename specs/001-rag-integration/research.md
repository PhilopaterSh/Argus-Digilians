# Research: RAG System Integration

## Embedding Model Comparison

| Model | Dimensions | Local | API Key | Speed | Quality |
|-------|-----------|-------|---------|-------|---------|
| nomic-embed-text (Ollama) | 768 | Yes | No | Fast | High |
| all-MiniLM-L6-v2 (HuggingFace) | 384 | Yes | No | Medium | Medium |
| text-embedding-3-small (OpenAI) | 1536 | No | Yes | Fast | Very High |

**Decision**: nomic-embed-text — best balance of quality, speed, and privacy (no API key, fully local).

## Chunking Strategy Research

| Strategy | Pros | Cons |
|----------|------|------|
| Fixed-size (RecursiveCharacter) | Simple, universal | Splits across semantic boundaries |
| Markdown headers | Preserves section integrity | Only works for .md files |
| JSON item split | Each item is a logical unit | Only works for list-of-objects JSON |
| CSV row split | Each row is a record | Loses column header context (we embed headers with row) |

**Decision**: Format-specific structural chunking — best semantic preservation per format type.

## Vector Database Comparison

| Database | Local | Persistence | Search Speed | Ease of Use |
|----------|-------|-------------|-------------|-------------|
| FAISS | Yes | File-based | Very Fast | Simple |
| Chroma | Yes | File-based | Fast | Simple |
| Pinecone | No | Cloud | Fast | Requires API key |
| Weaviate | Yes | Server-based | Fast | Heavy setup |

**Decision**: FAISS — lightweight, file-based, no server dependency, fastest search for local use.

## Fusion Strategy Research

| Strategy | Description | Risk |
|----------|-------------|------|
| Pre-fusion | Merge contexts before LLM call | Prompt size grows |
| Post-fusion | Retrieve, let LLM decide weighting | Hallucination from ignoring context |
| Instruction-gated | Static + Live + Priority instruction | Best control, clear separation |

**Decision**: Instruction-gated pre-fusion — explicit `===== STATIC KNOWLEDGE BASE =====` and `===== LIVE TARGET STATE =====` sections with priority instruction to favor live data.
