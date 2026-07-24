"""Unit tests for RAGEngine.query() threshold filtering and context fusion.

Uses a fake VectorStore (no FAISS) and mocked embeddings, so this exercises
RAGEngine's own logic without needing a live embedding backend or FAISS index.
"""
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.core.rag.config import RAGConfig
from app.core.rag.embeddings import EmbeddingFactory
from app.core.rag.rag_engine import RAGEngine

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_embedding_factory():
    """Reset the EmbeddingFactory singleton before and after each test."""
    EmbeddingFactory.reset()
    yield
    EmbeddingFactory.reset()


class _FakeVectorStore:
    def __init__(self, results):
        """Init  ."""
        self._results = results

    def load_index(self):
        """Load index."""
        return True

    def similarity_search(self, query, k=None):
        """Similarity search."""
        return [doc for doc, _ in self._results]

    def similarity_search_with_score(self, query, k=None):
        """Similarity search with score."""
        return self._results


def _make_engine(tmp_path, results, similarity_threshold=0.5):
    """Build a RAGEngine with mocked embeddings and a fake vector store returning `results`.

    Args:
        tmp_path: test parameter provided by this test's own setup (a
            pytest fixture or a mock/patch injected via a decorator - see
            the test's parameters/decorators for which).
        results: Canned `(Document, score)` pairs for the fake store to return.
        similarity_threshold (float): Passed to the engine's RAGConfig.

    Returns:
        RAGEngine: Configured with the fake vector store.
    """
    config = RAGConfig(
        similarity_threshold=similarity_threshold,
        vector_store_dir=str(tmp_path / "store"),
        knowledge_base_dir=str(tmp_path / "kb"),
        auto_rebuild=False,
    )
    with patch.object(EmbeddingFactory, "get_embeddings", return_value=MagicMock()):
        engine = RAGEngine(config=config)
    engine.vector_store = _FakeVectorStore(results)
    return engine


def test_query_filters_by_similarity_threshold(tmp_path):
    """Verify Query filters by similarity threshold.
    
    Args:
        tmp_path: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
    """
    good = Document(page_content="relevant chunk", metadata={"source": "a.md"})
    bad = Document(page_content="irrelevant chunk", metadata={"source": "b.md"})
    engine = _make_engine(tmp_path, [(good, 0.2), (bad, 0.9)])

    result = engine.query("q")

    assert result.chunks == ["relevant chunk"]
    assert len(result.sources) == 1
    assert len(result.all_chunks) == 2


def test_query_returns_no_results_message_when_nothing_passes_threshold(tmp_path):
    """Verify Query returns no results message when nothing passes threshold.
    
    Args:
        tmp_path: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
    """
    bad = Document(page_content="irrelevant", metadata={})
    engine = _make_engine(tmp_path, [(bad, 0.9)])

    result = engine.query("q")

    assert result.answer == "No relevant information found in the knowledge base."
    assert result.chunks == []


def test_format_combined_context_merges_rag_and_blackboard(tmp_path):
    """Verify Format combined context merges rag and blackboard.
    
    Args:
        tmp_path: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
    """
    doc = Document(page_content="rag chunk", metadata={"source": "a.md"})
    engine = _make_engine(tmp_path, [(doc, 0.1)])

    combined = engine.format_combined_context("q", blackboard_context="live findings")

    assert "STATIC KNOWLEDGE" in combined
    assert "LIVE TARGET STATE" in combined
    assert "live findings" in combined
    assert "rag chunk" in combined


def test_format_combined_context_blackboard_only_when_no_rag_matches(tmp_path):
    """Verify Format combined context blackboard only when no rag matches.
    
    Args:
        tmp_path: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
    """
    bad = Document(page_content="irrelevant", metadata={})
    engine = _make_engine(tmp_path, [(bad, 0.9)])

    combined = engine.format_combined_context("q", blackboard_context="live findings")

    assert "LIVE TARGET STATE" in combined
    assert "STATIC KNOWLEDGE" not in combined
