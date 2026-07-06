"""DEPRECATED shim. Canonical module: app.core.rag.vector_store (per 012 sec 2.1).

Retained only as a backward-compatible forwarder; scheduled for removal (012 T025).
No code should import this module.
"""
import warnings

from app.core.rag.vector_store import VectorStore

warnings.warn(
    "app.core.rag.vectorstore is deprecated; import "
    "app.core.rag.vector_store.VectorStore instead (012 sec 2.1).",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ['VectorStore']
