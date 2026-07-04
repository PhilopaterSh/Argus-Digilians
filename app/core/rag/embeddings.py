from typing import Optional
from app.core.rag.config import RAGConfig


class EmbeddingFactory:
    _instance = None
    _embedding_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_embeddings(cls, config: Optional[RAGConfig] = None):
        if cls._embedding_model is not None:
            return cls._embedding_model

        if config is None:
            config = RAGConfig.from_central()

        cls._embedding_model = cls._try_ollama(config)

        if cls._embedding_model is None:
            cls._embedding_model = cls._try_huggingface(config)

        if cls._embedding_model is None:
            cls._embedding_model = cls._try_openai()

        if cls._embedding_model is None:
            raise ImportError(
                "No embedding library available. "
                "Install langchain-ollama, langchain-huggingface, or langchain-openai"
            )

        return cls._embedding_model

    @classmethod
    def _try_ollama(cls, config: RAGConfig):
        try:
            from langchain_ollama import OllamaEmbeddings
            model = config.embedding_model
            print(f"[RAG] Using Ollama embeddings: {model}")
            return OllamaEmbeddings(
                model=model,
                base_url="http://localhost:11434",
            )
        except Exception as e:
            print(f"[RAG] Ollama embeddings unavailable ({e}), trying HuggingFace...")
            return None

    @classmethod
    def _try_huggingface(cls, config: RAGConfig):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            fallback = "all-MiniLM-L6-v2"
            print(f"[RAG] Using HuggingFace embeddings: {fallback}")
            return HuggingFaceEmbeddings(
                model_name=fallback,
                model_kwargs={"device": config.embedding_device},
            )
        except Exception as e:
            print(f"[RAG] HuggingFace unavailable ({e}), trying OpenAI...")
            return None

    @classmethod
    def _try_openai(cls):
        try:
            from langchain_openai import OpenAIEmbeddings
            print("[RAG] Using OpenAI embeddings: text-embedding-3-small")
            return OpenAIEmbeddings(model="text-embedding-3-small")
        except Exception as e:
            print(f"[RAG] OpenAI unavailable: {e}")
            return None

    @classmethod
    def reset(cls):
        cls._embedding_model = None
