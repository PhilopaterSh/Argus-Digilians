import logging
import os
from typing import TYPE_CHECKING, Any, List, Optional

from langchain_core.documents import Document

from app.core.rag import manifest as rag_manifest
from app.core.rag.config import RAGConfig
from app.core.rag.document_processor import DocumentProcessor
from app.core.rag.embeddings import EmbeddingFactory

if TYPE_CHECKING:
    from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, config: Optional[RAGConfig] = None):
        """Set up config/embeddings and ensure the vector store directory exists.

        Args:
            config (RAGConfig | None): Defaults to `RAGConfig.from_central()`.
        """
        self.config = config or RAGConfig.from_central()
        self.embeddings = EmbeddingFactory.get_embeddings(self.config)
        self._store: Optional["FAISS"] = None
        self._ensure_store_dir()

    def _ensure_store_dir(self):
        """Ensure store dir."""
        os.makedirs(self.config.vector_store_dir, exist_ok=True)

    @property
    def _index_path(self):
        """Index path."""
        return os.path.join(self.config.vector_store_dir, 'index.faiss')

    def build_index(self, chunks: List[Document]) -> int:
        """Build a fresh FAISS index from document chunks, persist it, and
        write its embedding manifest.

        Args:
            chunks (List[Document]): Chunks to index.

        Returns:
            int: Number of chunks indexed; 0 if `chunks` is empty (no
            index is built in that case).
        """
        if not chunks:
            logger.warning('[RAG] No chunks to index')
            return 0

        from langchain_community.vectorstores import FAISS

        self._store = FAISS.from_documents(chunks, self.embeddings)
        self._persist()
        rag_manifest.write_manifest(
            self.config.vector_store_dir,
            embedder_name=EmbeddingFactory.get_model_name() or self.config.embedding_model,
            embedder_provider=EmbeddingFactory.get_provider() or 'unknown',
            dimension=self._store.index.d,
            knowledge_base_dir=self.config.knowledge_base_dir,
        )
        logger.info('[RAG] Indexed %s chunks into FAISS', len(chunks))
        return len(chunks)

    def rebuild_from_directory(self, directory: Optional[str] = None) -> int:
        """Reprocess a directory into chunks and build a fresh index from them.

        Args:
            directory (str | None): Defaults to
                `self.config.knowledge_base_dir` (see `DocumentProcessor.
                process_directory`).

        Returns:
            int: Number of chunks indexed (see `build_index`).
        """
        processor = DocumentProcessor(self.config)
        chunks = processor.process_directory(directory)
        return self.build_index(chunks)

    def load_index(self) -> bool:
        """Load a persisted FAISS index from disk, if its manifest is still valid.

        Returns:
            bool: True if an existing, manifest-valid index was loaded
            into `self._store`; False if no index file exists, the
            manifest says a rebuild is needed (embedder or knowledge base
            changed), the pinned provider no longer matches the active
            one, or loading raised an exception.
        """
        if not os.path.exists(self._index_path):
            return False

        active_embedder_name = EmbeddingFactory.get_model_name() or self.config.embedding_model
        if rag_manifest.needs_rebuild(self.config.vector_store_dir, active_embedder_name, self.config.knowledge_base_dir):
            logger.warning(
                '[RAG] Manifest indicates the index is stale (embedder or knowledge base changed); '
                'skipping load so the caller can rebuild instead of querying a mismatched index.'
            )
            return False

        manifest = rag_manifest.read_manifest(self.config.vector_store_dir)
        active_provider = EmbeddingFactory.get_provider()
        if manifest is not None and active_provider is not None and manifest.embedder_provider != active_provider:
            logger.warning(
                '[RAG] Pinned embedder provider (%s) does not match the active provider (%s), '
                'e.g. Ollama became unavailable and HuggingFace was used as fallback; skipping stale index load.',
                manifest.embedder_provider, active_provider,
            )
            return False

        try:
            from langchain_community.vectorstores import FAISS

            self._store = FAISS.load_local(
                self.config.vector_store_dir,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            logger.info('[RAG] Loaded existing FAISS index from %s', self.config.vector_store_dir)
            return True
        except Exception as e:
            logger.warning('[RAG] Failed to load index: %s', e)
            return False

    def _persist(self):
        """Save the current in-memory FAISS index to `config.vector_store_dir`, if one exists."""
        if self._store is None:
            return
        self._store.save_local(self.config.vector_store_dir)
        logger.info('[RAG] Saved FAISS index to %s', self.config.vector_store_dir)

    def similarity_search(self, query: str, k: Optional[int] = None) -> List[Document]:
        """Search the index for the most similar documents, lazily loading it if needed.

        Args:
            query (str): The search query text.
            k (int | None): Max results; defaults to
                `self.config.retriever_k`.

        Returns:
            List[Document]: Matching documents, most similar first;
            empty if no index exists/can be loaded.
        """
        if self._store is None and not self.load_index():
            return []
        assert self._store is not None
        k = k or self.config.retriever_k
        return self._store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: Optional[int] = None) -> List[tuple]:
        """Like `similarity_search`, but each result is paired with its raw score.

        Args:
            query (str): The search query text.
            k (int | None): Max results; defaults to
                `self.config.retriever_k`.

        Returns:
            List[tuple]: `(Document, score)` pairs, most similar first;
            empty if no index exists/can be loaded.
        """
        if self._store is None and not self.load_index():
            return []
        assert self._store is not None
        k = k or self.config.retriever_k
        return self._store.similarity_search_with_score(query, k=k)

    def get_retriever(self, k: Optional[int] = None):
        """Return a LangChain retriever bound to this vector store, lazily loading it if needed.

        Args:
            k (int | None): Retriever's `search_kwargs["k"]`; defaults to
                `self.config.retriever_k`.

        Returns:
            A LangChain retriever (`FAISS.as_retriever(...)`).

        Raises:
            ValueError: If no index exists and none could be loaded.
        """
        if self._store is None and not self.load_index():
            raise ValueError('Vector store has not been initialized or loaded.')
        assert self._store is not None
        return self._store.as_retriever(search_kwargs={'k': k or self.config.retriever_k})

    @property
    def is_loaded(self) -> bool:
        """Is loaded."""
        return self._store is not None

    @property
    def index_size(self) -> int:
        """The number of vectors in the loaded index.

        Returns:
            int: `self._store.index.ntotal`, or 0 if no index is loaded.
        """
        if self._store is None:
            return 0
        return self._store.index.ntotal
