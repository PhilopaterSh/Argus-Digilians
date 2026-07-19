"""Regression tests for RAGEngine.add_document().

Real bug, confirmed live via `scripts/test_rag.py --smoke --no-llm`:
`DocumentProcessor.load_file()` returns `Optional[List[Document]]` (one
input file can legitimately produce multiple Document chunks - see
document_processor.py's structural chunking), but `add_document()` wrapped
that already-a-list return value in a second list
(`splitter.split_documents([doc])`), so `split_documents()` iterated once
and got the inner list itself where it expected a single `Document`,
crashing with `AttributeError: 'list' object has no attribute 'page_content'`.
"""
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.core.rag.config import RAGConfig
from app.core.rag.embeddings import EmbeddingFactory
from app.core.rag.rag_engine import RAGEngine


@pytest.fixture(autouse=True)
def _reset_embedding_factory():
    EmbeddingFactory.reset()
    yield
    EmbeddingFactory.reset()


class _FakeVectorStore:
    """Captures what add_document() passes to build_index(), without
    needing a real FAISS index/embedding backend."""
    def __init__(self):
        """Init  ."""
        self.build_index_calls = []

    def build_index(self, chunks):
        self.build_index_calls.append(list(chunks))
        return len(chunks)


def _make_engine(tmp_path):
    config = RAGConfig(
        vector_store_dir=str(tmp_path / "store"),
        knowledge_base_dir=str(tmp_path / "kb"),
        auto_rebuild=False,
    )
    with patch.object(EmbeddingFactory, "get_embeddings", return_value=MagicMock()):
        engine = RAGEngine(config=config)
    engine.vector_store = _FakeVectorStore()
    engine.initialize = MagicMock()  # avoid touching a real persisted index
    return engine


def test_add_document_ingests_a_real_markdown_file_without_crashing(tmp_path):
    """Verify Add document ingests a real markdown file without crashing.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    doc_path = tmp_path / "sample.md"
    doc_path.write_text("# Heading\n\nSome real content for the RAG smoke test.\n", encoding="utf-8")

    engine = _make_engine(tmp_path)
    result = engine.add_document(str(doc_path))

    assert result is True
    assert len(engine.vector_store.build_index_calls) == 1
    chunks = engine.vector_store.build_index_calls[0]
    assert len(chunks) >= 1
    # The exact bug this test locks in: chunks must be real Document
    # objects (with .page_content), not a list containing a nested list.
    for chunk in chunks:
        assert isinstance(chunk, Document)
        assert isinstance(chunk.page_content, str)
        assert len(chunk.page_content) > 0


def test_add_document_handles_a_file_that_splits_into_multiple_documents(tmp_path):
    """CSV loading produces one Document per row - a single input file
    legitimately producing >1 Document is exactly the shape that exposed
    the original bug (a single `doc` was never a bare Document).
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,note\nrow1,first note\nrow2,second note\n", encoding="utf-8")

    engine = _make_engine(tmp_path)
    result = engine.add_document(str(csv_path))

    assert result is True
    chunks = engine.vector_store.build_index_calls[0]
    assert len(chunks) >= 2  # at least one chunk per CSV row


def test_add_document_returns_false_for_unsupported_extension(tmp_path):
    """Verify Add document returns false for unsupported extension.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    bad_path = tmp_path / "sample.exe"
    bad_path.write_bytes(b"not a real document")

    engine = _make_engine(tmp_path)
    result = engine.add_document(str(bad_path))

    assert result is False
    assert engine.vector_store.build_index_calls == []


def test_add_document_returns_false_for_missing_file(tmp_path):
    """Verify Add document returns false for missing file.
    
    Args:
        tmp_path: pytest fixture (see the module's @pytest.fixture definitions).
    """
    engine = _make_engine(tmp_path)
    result = engine.add_document(str(tmp_path / "does_not_exist.md"))

    assert result is False
    assert engine.vector_store.build_index_calls == []
