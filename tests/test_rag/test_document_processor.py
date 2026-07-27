"""Unit tests for app/core/rag/document_processor.py::DocumentProcessor._load_json.

Regression test for a real, previously-untested bug: the non-list JSON
branch constructed `RecursiveJsonSplitter(max_doc_size=...)` (the real
kwarg is `max_chunk_size`), called `split_json()` with a JSON *string*
(it requires the parsed `dict`), and then treated its return value as a
list of strings (it actually returns `list[dict[str, Any]]`) when
building each `Document`'s `page_content`. Any of the three would raise
at runtime the moment a non-list JSON file was ever loaded into the
knowledge base - never exercised by any existing test, so it went
unnoticed until a full-repo mypy pass flagged all three mismatches.
"""
import json

import pytest

from app.core.rag.config import RAGConfig
from app.core.rag.document_processor import DocumentProcessor

pytestmark = pytest.mark.unit


def _make_processor(chunk_size=600):
    """Build a DocumentProcessor with a plain, dependency-free RAGConfig.

    Args:
        chunk_size (int): `RAGConfig.chunk_size` to use.

    Returns:
        DocumentProcessor: Configured with the given chunk size.
    """
    return DocumentProcessor(RAGConfig(chunk_size=chunk_size))


class TestLoadJsonNonListBranch:
    def test_small_json_object_splits_into_documents_with_string_page_content(self, tmp_path):
        """A JSON object (not a list) must be split via RecursiveJsonSplitter
        without raising, and every resulting Document.page_content must be
        a str, not the raw dict chunk RecursiveJsonSplitter.split_json()
        actually returns.

        Args:
            tmp_path (Path): Pytest's per-test temp directory fixture.
        """
        data = {"key1": "value1", "key2": {"nested": "value2"}}
        fpath = tmp_path / "small.json"
        fpath.write_text(json.dumps(data), encoding="utf-8")

        processor = _make_processor()
        docs = processor._load_json(str(fpath))

        assert len(docs) >= 1
        for doc in docs:
            assert isinstance(doc.page_content, str)
            assert doc.metadata["source"] == str(fpath)

    def test_large_json_object_splits_into_multiple_chunks(self, tmp_path):
        """A JSON object bigger than chunk_size must split into more than
        one Document, each still valid JSON text (round-trips via
        json.loads) - proves split_json() was called with the parsed dict,
        not a pre-serialized string it can't split top-level keys of.

        Args:
            tmp_path (Path): Pytest's per-test temp directory fixture.
        """
        data = {f"section_{i}": "x" * 200 for i in range(10)}
        fpath = tmp_path / "large.json"
        fpath.write_text(json.dumps(data), encoding="utf-8")

        processor = _make_processor(chunk_size=300)
        docs = processor._load_json(str(fpath))

        assert len(docs) > 1
        for doc in docs:
            json.loads(doc.page_content)

    def test_json_list_top_level_takes_the_other_branch_unaffected(self, tmp_path):
        """A list-rooted JSON file must still take the one-Document-per-item
        branch, untouched by this fix.

        Args:
            tmp_path (Path): Pytest's per-test temp directory fixture.
        """
        data = [{"a": 1}, {"b": 2}, {"c": 3}]
        fpath = tmp_path / "list.json"
        fpath.write_text(json.dumps(data), encoding="utf-8")

        processor = _make_processor()
        docs = processor._load_json(str(fpath))

        assert len(docs) == 3
        assert [doc.metadata["index"] for doc in docs] == [0, 1, 2]
