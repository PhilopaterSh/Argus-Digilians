"""Unit tests for the EmbeddingManifest wiring in VectorStore (specs/012 T029).

Uses mocked embeddings/FAISS throughout so this runs without a live Ollama
server, HuggingFace model download, or a real FAISS index.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from app.core.rag import manifest as rag_manifest
from app.core.rag.config import RAGConfig
from app.core.rag.embeddings import EmbeddingFactory
from app.core.rag.vector_store import VectorStore


@pytest.fixture(autouse=True)
def _reset_embedding_factory():
    EmbeddingFactory.reset()
    yield
    EmbeddingFactory.reset()


def _make_config(tmp_path, embedding_model="nomic-embed-text"):
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "doc.md").write_text("hello", encoding="utf-8")
    return RAGConfig(
        embedding_model=embedding_model,
        knowledge_base_dir=str(kb),
        vector_store_dir=str(tmp_path / "store"),
    )


class _FakeIndex:
    def __init__(self, dim):
        """Init  ."""
        self.index = MagicMock(d=dim)

    def save_local(self, path):
        """Save local."""
        pass


def _make_store(config):
    """Make store."""
    with patch.object(EmbeddingFactory, "get_embeddings", return_value=MagicMock()):
        return VectorStore(config)


def test_build_index_writes_manifest(tmp_path):
    """Verify Build index writes manifest.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    config = _make_config(tmp_path)
    EmbeddingFactory._provider = "ollama"
    EmbeddingFactory._model_name = "nomic-embed-text"
    store = _make_store(config)

    with patch("langchain_community.vectorstores.FAISS.from_documents", return_value=_FakeIndex(768)):
        count = store.build_index([MagicMock()])

    assert count == 1
    manifest = rag_manifest.read_manifest(config.vector_store_dir)
    assert manifest is not None
    assert manifest.embedder_name == "nomic-embed-text"
    assert manifest.embedder_provider == "ollama"
    assert manifest.dimension == 768


def test_load_index_proceeds_when_manifest_matches(tmp_path):
    """Verify Load index proceeds when manifest matches.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    config = _make_config(tmp_path)
    rag_manifest.write_manifest(
        config.vector_store_dir, "nomic-embed-text", "ollama", 768, config.knowledge_base_dir
    )
    os.makedirs(config.vector_store_dir, exist_ok=True)
    open(os.path.join(config.vector_store_dir, "index.faiss"), "w").close()

    EmbeddingFactory._provider = "ollama"
    EmbeddingFactory._model_name = "nomic-embed-text"
    store = _make_store(config)

    with patch("langchain_community.vectorstores.FAISS.load_local", return_value=_FakeIndex(768)) as mock_load:
        assert store.load_index() is True
        mock_load.assert_called_once()


def test_load_index_skips_when_provider_falls_back(tmp_path):
    """Ollama was used to build the index, but Ollama is now down and
    EmbeddingFactory silently fell back to HuggingFace: must not load the
    (now dimension-mismatched) stale index.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    config = _make_config(tmp_path)
    rag_manifest.write_manifest(
        config.vector_store_dir, "nomic-embed-text", "ollama", 768, config.knowledge_base_dir
    )
    os.makedirs(config.vector_store_dir, exist_ok=True)
    open(os.path.join(config.vector_store_dir, "index.faiss"), "w").close()

    EmbeddingFactory._provider = "huggingface"
    EmbeddingFactory._model_name = "all-MiniLM-L6-v2"
    store = _make_store(config)

    with patch("langchain_community.vectorstores.FAISS.load_local") as mock_load:
        assert store.load_index() is False
        mock_load.assert_not_called()


def test_load_index_skips_when_knowledge_base_changed(tmp_path):
    """Verify Load index skips when knowledge base changed.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    config = _make_config(tmp_path)
    rag_manifest.write_manifest(
        config.vector_store_dir, "nomic-embed-text", "ollama", 768, config.knowledge_base_dir
    )
    os.makedirs(config.vector_store_dir, exist_ok=True)
    open(os.path.join(config.vector_store_dir, "index.faiss"), "w").close()

    # knowledge base content changes after the index was built
    with open(os.path.join(config.knowledge_base_dir, "doc.md"), "w", encoding="utf-8") as f:
        f.write("changed content")

    EmbeddingFactory._provider = "ollama"
    EmbeddingFactory._model_name = "nomic-embed-text"
    store = _make_store(config)

    with patch("langchain_community.vectorstores.FAISS.load_local") as mock_load:
        assert store.load_index() is False
        mock_load.assert_not_called()


def test_load_index_returns_false_when_no_index_file(tmp_path):
    """Verify Load index returns false when no index file.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    config = _make_config(tmp_path)
    store = _make_store(config)
    assert store.load_index() is False
