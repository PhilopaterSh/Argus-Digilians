#!/usr/bin/env python
"""Ingest knowledge_base/ (including the 1000-scenario playbook) into the
FAISS vector store.

The scenario playbook (`knowledge_base/agent_playbook_scenarios.json`,
ported from the orphan branch `argus/momen`) is a JSON list, so
`DocumentProcessor._load_json` turns every scenario into its own Document
before chunking - giving the retriever per-scenario granularity instead of
one giant blob.

Usage:
    python scripts/ingest_scenarios_kb.py            # full rebuild + verify
    python scripts/ingest_scenarios_kb.py --no-verify  # skip retrieval checks

Note: the first run embeds every chunk (Ollama or the configured fallback
provider); expect a few minutes on CPU-only machines. Subsequent runs only
rebuild when the manifest detects knowledge-base changes.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.rag.config import RAGConfig
from app.core.rag.embeddings import EmbeddingFactory
from app.core.rag.vector_store import VectorStore

_VERIFY_QUERIES = [
    "Reflected XSS in a Next.js food delivery platform",
    "path traversal on an IIS server via filename parameter",
    "SQL injection behind Cloudflare WAF",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-verify", action="store_true",
                        help="skip post-build retrieval verification")
    args = parser.parse_args()

    config = RAGConfig()
    kb_dir = config.knowledge_base_dir
    if not os.path.isdir(kb_dir):
        print(f"[ingest] Knowledge base directory not found: {kb_dir}")
        return 1

    json_files = [f for f in os.listdir(kb_dir) if f.endswith(".json")]
    print(f"[ingest] Knowledge base: {kb_dir}")
    print(f"[ingest] JSON sources: {', '.join(json_files) or '(none)'}")

    provider = EmbeddingFactory.get_provider() or "not-selected-yet"
    model = EmbeddingFactory.get_model_name() or "?"
    print(f"[ingest] Embedding provider: {provider} ({model})")
    print("[ingest] Building index (first run can take minutes)...")

    store = VectorStore(config)
    try:
        chunk_count = store.rebuild_from_directory(kb_dir)
    except Exception as exc:  # pragma: no cover - operator-facing path
        print(f"[ingest] FAILED to build index: {exc}")
        return 1

    print(f"[ingest] Indexed {chunk_count} chunks "
          f"(index size: {store.index_size} vectors)")

    if args.no_verify:
        return 0

    failures = 0
    for query in _VERIFY_QUERIES:
        hits = store.similarity_search(query, k=2)
        if not hits:
            print(f"[verify] NO HITS for: {query!r}")
            failures += 1
            continue
        top = hits[0]
        snippet = " ".join(top.page_content.split())[:110]
        src = os.path.basename(str(top.metadata.get("source", "?")))
        print(f"[verify] {query!r} -> {src} :: {snippet}...")

    if failures:
        print(f"[ingest] Completed with {failures} verification failure(s)")
        return 1
    print("[ingest] Verification passed: scenario playbook is retrievable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
