"""Centralized configuration for the Argus Security Framework.

Reads `config/config.yaml` and provides typed access to all settings.
All components should import from here instead of hardcoding values.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class RAGSettings:
    enabled: bool = True
    embedding_model: str = "nomic-embed-text"
    embedding_device: str = "cpu"
    chunk_size: int = 600
    chunk_overlap: int = 100
    retriever_k: int = 4
    # Raised from 0.5 to 0.7 (2026-07-10) - live testing with the real
    # nomic-embed-text embeddings + FAISS L2 distance found 0.5 rejected
    # EVERY chunk for a query directly matching the knowledge base's own
    # content (closest real match scored 0.643, others ~1.0-1.08) - RAG was
    # silently contributing zero context on every live run, with no error
    # to indicate why. 0.7 admits that closest real match while still
    # rejecting the clearly-unrelated ~1.0+ chunks.
    similarity_threshold: float = 0.7
    auto_rebuild: bool = True
    knowledge_base_dir: str = "knowledge_base"


@dataclass
class StreamlitSettings:
    host: str = "localhost"
    port: int = 12199
    headless: bool = True
    enable_cors: bool = False
    enable_xsrf_protection: bool = False


@dataclass
class PathSettings:
    venv_python: str = "..\\Argus_venv\\Scripts\\python.exe"
    gui_entry: str = "..\\app\\GUI\\dashboard.py"


@dataclass
class LogSettings:
    level: str = "INFO"
    transformers_verbosity: str = "error"
    stream_log_level: str = "error"
    python_warnings: str = "ignore"


@dataclass
class ArgusConfig:
    log_level: str = "INFO"
    max_web_search_attempts: int = 3
    web_search_timeout_seconds: int = 10
    early_stopping_method: str = "stop"
    model_name: str = "hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M"
    command_timeout_seconds: int = 600
    recon_truncate_chars: int = 1000
    max_retries: int = 3
    # specs/019-shared-memory-reflection-upgrade: 3x self-consistency majority
    # vote on exploitation-tool results, scoped to EXPLOITATION_TOOLS in
    # react_workflow.py. Triples LLM calls for those specific tool calls only -
    # default on since local GGUF inference has no per-token API cost, but an
    # escape hatch in case it pushes a run past max_iterations' time budget in
    # practice (NFR-002).
    enable_inter_reflection: bool = True

    rag: RAGSettings = field(default_factory=RAGSettings)
    streamlit: StreamlitSettings = field(default_factory=StreamlitSettings)
    paths: PathSettings = field(default_factory=PathSettings)
    logging: LogSettings = field(default_factory=LogSettings)

    _instance: Optional["ArgusConfig"] = None

    @classmethod
    def load(cls, path: Optional[str] = None) -> "ArgusConfig":
        if cls._instance is not None:
            return cls._instance

        if path is None:
            path = os.getenv("ARGUS_CONFIG", "config/config.yaml")

        cfg = cls()
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                cfg._apply(raw)
            except Exception as e:
                print(f"[CONFIG] Failed to load {path}: {e}")

        cls._instance = cfg
        return cfg

    @classmethod
    def reset(cls):
        """Reset."""
        cls._instance = None

    def _apply(self, raw: dict):
        """Apply."""
        for key, value in raw.items():
            if key == "rag" and isinstance(value, dict):
                for k, v in value.items():
                    if hasattr(self.rag, k):
                        setattr(self.rag, k, v)
            elif key == "streamlit" and isinstance(value, dict):
                for k, v in value.items():
                    normalized = self._snake(k)
                    if hasattr(self.streamlit, normalized):
                        setattr(self.streamlit, normalized, v)
            elif key == "paths" and isinstance(value, dict):
                for k, v in value.items():
                    normalized = self._snake(k)
                    if hasattr(self.paths, normalized):
                        setattr(self.paths, normalized, v)
            elif key == "logging" and isinstance(value, dict):
                for k, v in value.items():
                    normalized = self._snake(k)
                    if hasattr(self.logging, normalized):
                        setattr(self.logging, normalized, v)
            elif hasattr(self, key):
                setattr(self, key, value)

    @staticmethod
    def _snake(name: str) -> str:
        """Snake."""
        return name.replace("-", "_").lower()

    def to_rag_dict(self) -> dict:
        """To rag dict."""
        return {
            "enabled": self.rag.enabled,
            "embedding_model": self.rag.embedding_model,
            "embedding_device": self.rag.embedding_device,
            "chunk_size": self.rag.chunk_size,
            "chunk_overlap": self.rag.chunk_overlap,
            "retriever_k": self.rag.retriever_k,
            "similarity_threshold": self.rag.similarity_threshold,
            "auto_rebuild": self.rag.auto_rebuild,
            "knowledge_base_dir": self.rag.knowledge_base_dir,
            "vector_store_dir": os.path.join(
                os.getcwd(), "app", "core", "rag", "store"
            ),
        }
