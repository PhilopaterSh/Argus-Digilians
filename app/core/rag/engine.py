"""DEPRECATED shim. Canonical module: app.core.rag.rag_engine (per 012 sec 2.1).

Retained only as a backward-compatible forwarder; scheduled for removal (012 T025).
No code should import this module.
"""
import warnings

from app.core.rag.rag_engine import RAGEngine, RAGResult

warnings.warn(
    "app.core.rag.engine is deprecated; import "
    "app.core.rag.rag_engine.RAGEngine instead (012 sec 2.1).",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ['RAGEngine', 'RAGResult']
