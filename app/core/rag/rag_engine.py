import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_factory import build_llm
from app.core.rag.config import RAGConfig
from app.core.rag.document_processor import DocumentProcessor
from app.core.rag.embeddings import EmbeddingFactory
from app.core.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    answer: str
    sources: List[Dict[str, Any]]
    chunks: List[str]
    all_chunks: List[str]


RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are an AI penetration testing assistant. Use the provided context to answer the question.

Context from knowledge base:
{context}

Question: {question}

Instructions:
- Answer based strictly on the provided context.
- If the context does not contain enough information, say so clearly.
- Reference specific sources when possible.
- Keep the answer technical and actionable.

Answer:"""
)


RAG_PROMPT_SUMMARIZE = ChatPromptTemplate.from_template(
    """Summarize the following context in a concise technical manner:

{context}

Focus on:
- Key technical findings
- Vulnerabilities or security issues mentioned
- Tools and techniques referenced
- Actionable intelligence

Summary:"""
)


class RAGEngine:
    def __init__(self, config: Optional[RAGConfig] = None, model_name: Optional[str] = None):
        self.config = config or RAGConfig.from_central()
        self.embeddings = EmbeddingFactory.get_embeddings(self.config)
        self.processor = DocumentProcessor(self.config)
        self.vector_store = VectorStore(self.config)
        self.llm = build_llm(model_name) if model_name else None
        self._initialized = False

    def initialize(self, rebuild: Optional[bool] = None):
        if self._initialized:
            return

        should_rebuild = rebuild if rebuild is not None else self.config.auto_rebuild
        index_loaded = self.vector_store.load_index()

        if should_rebuild or not index_loaded:
            count = self.vector_store.rebuild_from_directory()
            if count > 0:
                self._initialized = True
        elif index_loaded:
            self._initialized = True

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        self.initialize()
        return self.vector_store.similarity_search(query, k=k)

    def retrieve_with_scores(self, query: str, k: Optional[int] = None) -> List[tuple]:
        self.initialize()
        return self.vector_store.similarity_search_with_score(query, k=k)

    def augment(self, query: str, context_chunks: List[str]) -> str:
        context = "\n\n---\n\n".join(context_chunks)
        if self.llm is None:
            return context

        chain = RAG_PROMPT | self.llm | StrOutputParser()
        return chain.invoke({"context": context, "question": query})

    def query(self, query: str, k: Optional[int] = None) -> RAGResult:
        self.initialize()

        results = self.vector_store.similarity_search_with_score(query, k=k)

        chunks: List[str] = []
        sources: List[Dict[str, Any]] = []
        all_chunks = [doc.page_content for doc, _ in results]

        for doc, score in results:
            if score <= self.config.similarity_threshold:
                sources.append(
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score,
                    }
                )
                chunks.append(doc.page_content)

        if not chunks:
            return RAGResult(
                answer="No relevant information found in the knowledge base.",
                sources=[],
                chunks=[],
                all_chunks=all_chunks,
            )

        answer = self.augment(query, chunks)

        return RAGResult(
            answer=answer,
            sources=sources,
            chunks=chunks,
            all_chunks=all_chunks,
        )

    def query_relevant(self, query: str, k: Optional[int] = None) -> str:
        result = self.query(query, k=k)
        return result.answer

    def add_document(self, file_path: str) -> bool:
        doc = self.processor.load_file(file_path)
        if doc is None:
            return False

        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        chunks = splitter.split_documents([doc])

        self.initialize(rebuild=False)
        count = self.vector_store.build_index(chunks)
        return count > 0

    def rebuild_index(self):
        self._initialized = False
        self.vector_store = VectorStore(self.config)
        self.initialize(rebuild=True)

    def format_context(self, query: str, k: Optional[int] = None) -> str:
        results = self.retrieve(query, k=k)
        if not results:
            return ""

        return "\n\n---\n\n".join(
            f"[Source: {os.path.basename(d.metadata.get('source', 'unknown'))}]\n{d.page_content}"
            for d in results
        )

    def format_combined_context(self, query: str, blackboard_context: str = "", k: Optional[int] = None) -> str:
        rag_context = self.format_context(query, k=k)
        parts = []

        if rag_context:
            parts.append(
                "===== STATIC KNOWLEDGE BASE (techniques, cheatsheets, general knowledge) =====\n"
                f"{rag_context}"
            )

        if blackboard_context:
            parts.append(
                "===== LIVE TARGET STATE (current findings from active reconnaissance) =====\n"
                f"{blackboard_context}"
            )

        if not parts:
            return ""

        return "\n\n".join(parts)
