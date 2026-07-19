"""Unit tests for app.core.rag.manifest (EmbeddingManifest).

Covers specs/012-spec-reconciliation/data-model.md acceptance criteria AC-1 and
the deterministic-rebuild rule (spec.md section 3, FR-C1..C3). Standard-library
only - no FAISS / Ollama required, so this runs in CI without external services.
"""
import importlib.util
import json
import os
import pathlib
import sys

import pytest

# Load the leaf module directly by path so this unit test does NOT trigger
# app/core/rag/__init__.py (which eagerly imports langchain). The manifest module
# is standard-library only and testable in isolation, in CI and locally.
_MANIFEST_PATH = pathlib.Path(__file__).resolve().parents[2] / "app" / "core" / "rag" / "manifest.py"
_spec = importlib.util.spec_from_file_location("argus_rag_manifest", _MANIFEST_PATH)
m = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = m  # register before exec (dataclass + future-annotations needs it)
_spec.loader.exec_module(m)

pytestmark = pytest.mark.unit


def _make_kb(tmp_path, text="alpha"):
    kb = tmp_path / "knowledge_base"
    kb.mkdir()
    (kb / "doc.md").write_text(text, encoding="utf-8")
    return str(kb)


def test_write_then_read_round_trip(tmp_path):
    """Verify Write then read round trip.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    store = str(tmp_path / "store")
    kb = _make_kb(tmp_path)
    written = m.write_manifest(store, "nomic-embed-text", "ollama", 768, kb)
    assert os.path.isfile(m.manifest_path(store))
    loaded = m.read_manifest(store)
    assert loaded is not None
    assert loaded.embedder_name == "nomic-embed-text"
    assert loaded.embedder_provider == "ollama"
    assert loaded.dimension == 768
    assert loaded.knowledge_base_hash == written.knowledge_base_hash
    assert loaded.schema_version == m.SCHEMA_VERSION


def test_read_missing_returns_none(tmp_path):
    """Verify Read missing returns none."""
    assert m.read_manifest(str(tmp_path / "nope")) is None


def test_read_corrupt_returns_none(tmp_path):
    """Verify Read corrupt returns none.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    store = tmp_path / "store"
    store.mkdir()
    (store / m.MANIFEST_FILENAME).write_text("{ not json", encoding="utf-8")
    assert m.read_manifest(str(store)) is None


def test_needs_rebuild_when_no_manifest(tmp_path):
    """Verify Needs rebuild when no manifest.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    kb = _make_kb(tmp_path)
    assert m.needs_rebuild(str(tmp_path / "store"), "nomic-embed-text", kb) is True


def test_no_rebuild_when_unchanged(tmp_path):
    """Verify No rebuild when unchanged.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    store = str(tmp_path / "store")
    kb = _make_kb(tmp_path)
    m.write_manifest(store, "nomic-embed-text", "ollama", 768, kb)
    assert m.needs_rebuild(store, "nomic-embed-text", kb) is False


def test_rebuild_when_embedder_changes(tmp_path):
    """Verify Rebuild when embedder changes.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    store = str(tmp_path / "store")
    kb = _make_kb(tmp_path)
    m.write_manifest(store, "nomic-embed-text", "ollama", 768, kb)
    # switching to a different-dimension embedder MUST force a rebuild (AC-1)
    assert m.needs_rebuild(store, "all-MiniLM-L6-v2", kb) is True


def test_rebuild_when_kb_content_changes(tmp_path):
    """Verify Rebuild when kb content changes.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    store = str(tmp_path / "store")
    kb = _make_kb(tmp_path, text="alpha")
    m.write_manifest(store, "nomic-embed-text", "ollama", 768, kb)
    # mutate the knowledge base content
    with open(os.path.join(kb, "doc.md"), "w", encoding="utf-8") as f:
        f.write("beta-changed")
    assert m.needs_rebuild(store, "nomic-embed-text", kb) is True


def test_kb_hash_is_stable_across_calls(tmp_path):
    """Verify Kb hash is stable across calls.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    kb = _make_kb(tmp_path)
    assert m.compute_kb_hash(kb) == m.compute_kb_hash(kb)


def test_missing_kb_hashes_to_sentinel(tmp_path):
    """Verify Missing kb hashes to sentinel.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    h = m.compute_kb_hash(str(tmp_path / "absent"))
    assert isinstance(h, str) and len(h) == 64


def test_manifest_json_is_ascii(tmp_path):
    """Verify Manifest json is ascii.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    store = str(tmp_path / "store")
    kb = _make_kb(tmp_path)
    m.write_manifest(store, "nomic-embed-text", "ollama", 768, kb)
    raw = open(m.manifest_path(store), "rb").read()
    assert all(b < 128 for b in raw)
    # and it is valid JSON with the required keys
    data = json.loads(raw.decode("ascii"))
    for key in ("embedder_name", "embedder_provider", "dimension",
                "knowledge_base_hash", "built_at", "schema_version"):
        assert key in data
