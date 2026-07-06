# RAG System in Argus Framework

## What is RAG?

RAG = **R**etrieval-**A**ugmented **G**eneration.

Instead of asking the AI to answer from its training memory alone (which may be outdated or generic), we first **retrieve** relevant information from a local knowledge base, then **augment** the AI's prompt with that information, and finally let the AI **generate** a precise answer.

```
User Question
      │
      ▼
┌─────────────┐     ┌──────────────────┐
│  RETRIEVE   │────▶│   Knowledge Base  │
│  (FAISS)    │     │  (knowledge_base/)│
└─────────────┘     └──────────────────┘
      │
      ▼
┌─────────────┐
│   AUGMENT   │────▶ Combine: Context + Question
└─────────────┘
      │
      ▼
┌─────────────┐
│  GENERATE   │────▶ Ollama LLM answers with context
│  (Ollama)   │
└─────────────┘
```

---

## Why does Argus need RAG?

Argus is an AI penetration testing framework. During a pentest, the AI needs two types of information:

| Type | Source | Example |
|------|--------|---------|
| **Static Knowledge** | RAG (FAISS) | "How to exploit Apache 2.4.49", "SQL injection cheatsheet", "WAF bypass techniques" |
| **Live Target State** | Blackboard (SQLite) | "Target X has port 443 open", "We found Apache 2.4.49 on this server", "Previous scan found SQLi on /login" |

Before RAG, Argus relied only on the LLM's training data (static) and the SQLite Blackboard (live). Now it also searches a local vector database of technical documents to ground its decisions in verified knowledge.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Argus Framework                           │
│                                                              │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────┐   │
│  │ ArgusBrain│───▶│  RAG Engine      │◀──▶│  FAISS Store  │   │
│  │ (brain.py)│    │  (rag_engine.py) │    │  (vector)     │   │
│  └─────┬────┘    └──────────────────┘    └───────┬───────┘   │
│        │                                         │           │
│        │         ┌──────────────────┐            │           │
│        └────────▶│  Blackboard      │            │           │
│                  │  (SQLite Memory) │            │           │
│                  └──────────────────┘            │           │
│                                                  │           │
│                                      ┌───────────▼───────┐   │
│                                      │  knowledge_base/  │   │
│                                      │  (.md .json .csv) │   │
│                                      └───────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## How it works step by step

### Step 1: User asks a question
```
User: "What vulnerabilities does target X have?"
```

### Step 2: Brain refreshes live state
ArgusBrain calls `_refresh_blackboard()`:
- Reads **Blackboard** (SQLite): current findings about target X
- Reads **Knowledge Graph**: relationships between entities

### Step 3: Brain retrieves static knowledge
ArgusBrain calls `_enrich_with_rag()`:
- `RAGEngine` searches **FAISS** vector store
- Finds top 4 most relevant document chunks
- Each chunk has a similarity score

### Step 4: Brain fuses both contexts
`format_combined_context()` merges:

```
===== STATIC KNOWLEDGE BASE (techniques, cheatsheets) =====
[Apache 2.4.49 - Path Traversal CVE-2021-41773]
[SQL Injection bypass techniques...]

===== LIVE TARGET STATE (active reconnaissance findings) =====
[Blackboard Intelligence]
Target X: { ports: [80, 443], tech: [Apache 2.4.49] }

[Knowledge Graph Relations]
(target-x) --[HOSTS]--> (Apache 2.4.49)
```

### Step 5: AI reasons with full context
The enriched prompt is sent to Ollama LLM with instructions:
- Prioritize **live target state** over **static knowledge**
- If they contradict, flag the discrepancy

### Step 6: AI executes tools and persists findings
- Brain selects a tool (e.g., `run_nikto`)
- Tool executes via WSL/Kali
- Results are stored back to Blackboard (SQLite)
- Next query will include this new intelligence

---

## Embedding Model

Argus uses **nomic-embed-text** via Ollama as its embedding model.

- Runs **locally** — no API key, no data leaves your machine
- **768-dimension** embeddings for high retrieval accuracy
- Automatically loaded when the RAG engine initializes

> If Ollama is unavailable, the system falls back to HuggingFace (all-MiniLM-L6-v2), then OpenAI (text-embedding-3-small). These are edge-case safeguards, not the intended configuration.

---

## Document Processing: Structural Chunking

Not all files are split the same way. Each format keeps its meaning:

| Format | Method | Example |
|--------|--------|---------|
| **Markdown** | Split by headers (#, ##, ###) | Each section stays together |
| **JSON (list)** | Each array item = 1 document | `[item1, item2, ...]` |
| **JSON (object)** | RecursiveJsonSplitter | Split by size, keep structure |
| **CSV** | Row by row | Each row = key:value pairs |
| **PDF** | Page by page | PyPDFLoader |
| **TXT, YAML, HTML** | Fixed-size chunks (600 chars) | With 100 char overlap |

---

## Project Structure

```
Argus/
├── app/core/rag/               ← RAG system (this module)
│   ├── __init__.py              Exports
│   ├── config.py                Settings (model, chunk size, etc.)
│   ├── embeddings.py            Embedding model factory
│   ├── document_processor.py    Load + chunk documents
│   ├── vector_store.py          FAISS index management
│   └── rag_engine.py            Main query engine
│
├── knowledge_base/              ← Source documents for RAG
│   └── argus_security_knowledge.md
│
├── app/core/agent/brain.py      ← ArgusBrain (single canonical Brain; per 012 sec 2.2)
└── config.yaml                  ← RAG settings
```

---

## Key Features

- **Works offline**: nomic-embed-text runs locally via Ollama
- **Deterministic rebuild**: FAISS index rebuilds when the knowledge_base content hash OR the pinned embedder differs from store/manifest.json (per 012 sec 3)
- **One embedder per index**: the HuggingFace/OpenAI fallback runs only at BUILD time to pick an available embedder, which is pinned in the manifest; if that embedder is unavailable at query time, RAG degrades to Blackboard-only rather than querying a dimension-mismatched index (no query-time cross-dimension substitution)
- **Context-aware**: Separates static knowledge from live target data
- **Format-aware**: Structural chunking preserves document meaning
- **Non-blocking**: If RAG fails, falls back to Blackboard-only or raw query

---

## Configuration (config.yaml)

```yaml
rag:
  enabled: true
  embedding_model: "nomic-embed-text"
  embedding_device: "cpu"
  chunk_size: 600
  chunk_overlap: 100
  retriever_k: 4
  similarity_threshold: 0.5
  auto_rebuild: true
  knowledge_base_dir: "knowledge_base"
```

---

## Adding new knowledge

Simply place files in `knowledge_base/`:

```
knowledge_base/
├── cheatsheets/
│   ├── sql_injection.md
│   └── xss_payloads.json
├── cve_notes/
│   └── apache_vulnerabilities.csv
└── techniques/
    └── waf_bypass.pdf
```

The system will automatically detect, process, chunk, embed, and index them on the next query.
