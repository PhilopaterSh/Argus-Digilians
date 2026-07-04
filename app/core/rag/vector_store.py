import logging
import os
from typing import List, Optional

from langchain_core.documents import Document

from app.core.rag.config import RAGConfig
from app.core.rag.document_processor import DocumentProcessor
from app.core.rag.embeddings import EmbeddingFactory

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig.from_central()
        self.embeddings = EmbeddingFactory.get_embeddings(self.config)
        self._store = None
        self._ensure_store_dir()

    def _ensure_store_dir(self):
        os.makedirs(self.config.vector_store_dir, exist_ok=True)

    @property
    def _index_path(self):
        return os.path.join(self.config.vector_store_dir, 'index.faiss')

    def build_index(self, chunks: List[Document]) -> int:
        if not chunks:
            logger.warning('[RAG] No chunks to index')
            return 0

        from langchain_community.vectorstores import FAISS

        self._store = FAISS.from_documents(chunks, self.embeddings)
        self._persist()
        logger.info('[RAG] Indexed %s chunks into FAISS', len(chunks))
        return len(chunks)

    def rebuild_from_directory(self, directory: Optional[str] = None) -> int:
        processor = DocumentProcessor(self.config)
        chunks = processor.process_directory(directory)
        return self.build_index(chunks)

    def load_index(self) -> bool:
        if not os.path.exists(self._index_path):
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
        if self._store is None:
            return
        self._store.save_local(self.config.vector_store_dir)
        logger.info('[RAG] Saved FAISS index to %s', self.config.vector_store_dir)

    def similarity_search(self, query: str, k: Optional[int] = None) -> List[Document]:
        if self._store is None and not self.load_index():
            return []
        k = k or self.config.retriever_k
        return self._store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: Optional[int] = None) -> List[tuple]:
        if self._store is None and not self.load_index():
            return []
        k = k or self.config.retriever_k
        return self._store.similarity_search_with_score(query, k=k)

    def get_retriever(self, k: Optional[int] = None):
        if self._store is None and not self.load_index():
            raise ValueError('Vector store has not been initialized or loaded.')
        return self._store.as_retriever(search_kwargs={'k': k or self.config.retriever_k})

    @property
    def is_loaded(self) -> bool:
        return self._store is not None

    @property
    def index_size(self) -> int:
        if self._store is None:
            return 0
        return self._store.index.ntotal
