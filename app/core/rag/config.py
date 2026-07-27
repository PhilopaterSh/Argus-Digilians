from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class RAGConfig:
    embedding_model: str = "nomic-embed-text"
    embedding_device: str = "cpu"
    chunk_size: int = 600
    chunk_overlap: int = 100
    retriever_k: int = 4
    knowledge_base_dir: str = field(default_factory=lambda: os.path.join(
        os.getcwd(), "knowledge_base"
    ))
    vector_store_dir: str = field(default_factory=lambda: os.path.join(
        os.getcwd(), "app", "core", "rag", "store"
    ))
    auto_rebuild: bool = True
    # Raised from 0.5 to 0.7 (2026-07-10) - see app/core/config.py::RAGSettings's
    # matching comment for the live measurement that motivated this.
    similarity_threshold: float = 0.7

    @classmethod
    def from_central(cls) -> "RAGConfig":
        """Build a RAGConfig from the project-wide ArgusConfig's `rag` section.

        Returns:
            RAGConfig: A new instance populated from ArgusConfig.load().rag,
            with `vector_store_dir` always forced to the fixed
            `app/core/rag/store` path regardless of what ArgusConfig says.
        """
        from app.core.config import ArgusConfig
        cfg = ArgusConfig.load()
        return cls(
            embedding_model=cfg.rag.embedding_model,
            embedding_device=cfg.rag.embedding_device,
            chunk_size=cfg.rag.chunk_size,
            chunk_overlap=cfg.rag.chunk_overlap,
            retriever_k=cfg.rag.retriever_k,
            knowledge_base_dir=cfg.rag.knowledge_base_dir,
            vector_store_dir=os.path.join(os.getcwd(), "app", "core", "rag", "store"),
            auto_rebuild=cfg.rag.auto_rebuild,
            similarity_threshold=cfg.rag.similarity_threshold,
        )

    @classmethod
    def from_dict(cls, config_dict: Optional[dict] = None) -> "RAGConfig":
        """Build a RAGConfig from a plain dict, falling back field-by-field
        to this dataclass's own hardcoded defaults for any missing key.

        Args:
            config_dict (dict | None): Overrides, keyed by field name; if
                `None` entirely, delegates to `from_central()` instead (not
                to the dataclass defaults used for a partial dict).

        Returns:
            RAGConfig: A new instance with each field taken from
            `config_dict` if present, else from `cls()`'s dataclass
            defaults.
        """
        if config_dict is None:
            return cls.from_central()

        defaults = cls()
        return cls(
            embedding_model=config_dict.get("embedding_model", defaults.embedding_model),
            embedding_device=config_dict.get("embedding_device", defaults.embedding_device),
            chunk_size=config_dict.get("chunk_size", defaults.chunk_size),
            chunk_overlap=config_dict.get("chunk_overlap", defaults.chunk_overlap),
            retriever_k=config_dict.get("retriever_k", defaults.retriever_k),
            knowledge_base_dir=config_dict.get("knowledge_base_dir", defaults.knowledge_base_dir),
            vector_store_dir=config_dict.get("vector_store_dir", defaults.vector_store_dir),
            auto_rebuild=config_dict.get("auto_rebuild", defaults.auto_rebuild),
            similarity_threshold=config_dict.get("similarity_threshold", defaults.similarity_threshold),
        )

