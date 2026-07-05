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
    similarity_threshold: float = 0.5

    @classmethod
    def from_dict(cls, config_dict: Optional[dict] = None) -> "RAGConfig":
        if config_dict is None:
            return cls()
        return cls(
            embedding_model=config_dict.get("embedding_model", cls.embedding_model),
            embedding_device=config_dict.get("embedding_device", cls.embedding_device),
            chunk_size=config_dict.get("chunk_size", cls.chunk_size),
            chunk_overlap=config_dict.get("chunk_overlap", cls.chunk_overlap),
            retriever_k=config_dict.get("retriever_k", cls.retriever_k),
            knowledge_base_dir=config_dict.get("knowledge_base_dir", cls.knowledge_base_dir),
            vector_store_dir=config_dict.get("vector_store_dir", cls.vector_store_dir),
            auto_rebuild=config_dict.get("auto_rebuild", cls.auto_rebuild),
            similarity_threshold=config_dict.get("similarity_threshold", cls.similarity_threshold),
        )
