"""DEPRECATED shim. Canonical module: app.core.rag.document_processor (per 012 sec 2.1).

Retained only as a backward-compatible forwarder; scheduled for removal (012 T025).
No code should import this module.
"""
import warnings

from app.core.rag.document_processor import DocumentProcessor

warnings.warn(
    "app.core.rag.processor is deprecated; import "
    "app.core.rag.document_processor.DocumentProcessor instead (012 sec 2.1).",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ['DocumentProcessor']
