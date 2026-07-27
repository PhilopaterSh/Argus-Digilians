"""EmbeddingManifest - one embedder per FAISS index (canonical RAG design).

Implements specs/012-spec-reconciliation/spec.md section 3 (FR-C1..C5) and
specs/012-spec-reconciliation/data-model.md Entity 1.

A FAISS index has a fixed vector dimensionality, so an index MUST be pinned to a
single embedder. This module records the pinned embedder in
`<store_dir>/manifest.json` and decides deterministically whether a rebuild is
required (knowledge_base content hash OR embedder changed). It is intentionally
dependency-free (standard library only) so it can be imported and unit-tested
without FAISS / langchain / Ollama installed.

Integration (see tasks.md T029): VectorStore writes a manifest after building an
index; RAGEngine calls `needs_rebuild()` on load and, if the pinned embedder is
unavailable and no rebuild is possible, degrades to Blackboard-only rather than
querying a dimension-mismatched index.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

MANIFEST_FILENAME = "manifest.json"
SCHEMA_VERSION = 1
_HASH_EXTS = (".md", ".txt", ".json", ".csv", ".pdf", ".yaml", ".yml", ".html")


@dataclass
class EmbeddingManifest:
    """Metadata pinning one FAISS index to one embedder."""
    embedder_name: str
    embedder_provider: str  # ollama | huggingface | openai
    dimension: int
    knowledge_base_hash: str
    built_at: str = ""
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict:
        """To dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingManifest":
        """From dict."""
        return cls(
            embedder_name=str(data["embedder_name"]),
            embedder_provider=str(data["embedder_provider"]),
            dimension=int(data["dimension"]),
            knowledge_base_hash=str(data["knowledge_base_hash"]),
            built_at=str(data.get("built_at", "")),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )


def compute_kb_hash(knowledge_base_dir: str) -> str:
    """Return a stable content hash of the knowledge base directory.

    Hashes relative paths + file bytes for all recognised source files, in sorted
    order, so the same content always yields the same hash regardless of walk order.
    A missing directory hashes to a fixed sentinel (empty knowledge base).

    Args:
        knowledge_base_dir (str): Directory to hash.

    Returns:
        str: A SHA-256 hex digest.
    """
    h = hashlib.sha256()
    if not os.path.isdir(knowledge_base_dir):
        h.update(b"__NO_KB__")
        return h.hexdigest()
    files = []
    for dp, _dn, fn in os.walk(knowledge_base_dir):
        for f in fn:
            if f.lower().endswith(_HASH_EXTS):
                files.append(os.path.join(dp, f))
    for path in sorted(files):
        rel = os.path.relpath(path, knowledge_base_dir).replace(os.sep, "/")
        h.update(rel.encode("utf-8"))
        try:
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
        except OSError:
            # Unreadable file: record its path only, do not fail the build.
            h.update(b"__UNREADABLE__")
    return h.hexdigest()


def manifest_path(store_dir: str) -> str:
    """Manifest path."""
    return os.path.join(store_dir, MANIFEST_FILENAME)


def write_manifest(store_dir: str, embedder_name: str, embedder_provider: str,
                   dimension: int, knowledge_base_dir: str) -> EmbeddingManifest:
    """Build and persist a manifest for a freshly built index.

    Args:
        store_dir (str): Directory to write `manifest.json` into (created
            if missing).
        embedder_name (str): Name of the embedder used to build the index.
        embedder_provider (str): "ollama" | "huggingface" | "openai".
        dimension (int): The index's vector dimensionality.
        knowledge_base_dir (str): Source directory to hash via
            `compute_kb_hash`.

    Returns:
        EmbeddingManifest: The manifest that was written.
    """
    os.makedirs(store_dir, exist_ok=True)
    manifest = EmbeddingManifest(
        embedder_name=embedder_name,
        embedder_provider=embedder_provider,
        dimension=int(dimension),
        knowledge_base_hash=compute_kb_hash(knowledge_base_dir),
        built_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        schema_version=SCHEMA_VERSION,
    )
    with open(manifest_path(store_dir), "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2, sort_keys=True)
    return manifest


def read_manifest(store_dir: str) -> EmbeddingManifest | None:
    """Load a manifest, or None if it is absent or unreadable/corrupt.

    Args:
        store_dir (str): Directory to look for `manifest.json` in.

    Returns:
        EmbeddingManifest | None: The parsed manifest, or `None` if the
        file doesn't exist or fails to parse (OSError/ValueError/KeyError).
    """
    path = manifest_path(store_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return EmbeddingManifest.from_dict(json.load(f))
    except (OSError, ValueError, KeyError):
        return None


def needs_rebuild(store_dir: str, embedder_name: str, knowledge_base_dir: str) -> bool:
    """Return True if the index must be rebuilt.

    Rebuild is required when: no manifest exists, the schema version differs, the
    pinned embedder differs from the requested one, or the knowledge base content
    hash has changed.

    Args:
        store_dir (str): Directory containing (or missing) `manifest.json`.
        embedder_name (str): The embedder currently in use, compared
            against the manifest's pinned `embedder_name`.
        knowledge_base_dir (str): Source directory to re-hash for
            comparison against the manifest's stored hash.

    Returns:
        bool: True if a rebuild is needed, False if the existing index
        can be safely reused as-is.
    """
    manifest = read_manifest(store_dir)
    if manifest is None:
        return True
    if manifest.schema_version != SCHEMA_VERSION:
        return True
    if manifest.embedder_name != embedder_name:
        return True
    if manifest.knowledge_base_hash != compute_kb_hash(knowledge_base_dir):
        return True
    return False
