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
        """Wire up the config, embeddings, document processor, and vector store.

        Args:
            config (RAGConfig | None): Defaults to `RAGConfig.from_central()`.
            model_name (str | None): If given, builds an LLM (via
                `build_llm`) for `augment()`'s answer synthesis; if
                omitted, `augment()` falls back to returning raw context.
        """
        self.config = config or RAGConfig.from_central()
        self.embeddings = EmbeddingFactory.get_embeddings(self.config)
        self.processor = DocumentProcessor(self.config)
        self.vector_store = VectorStore(self.config)
        self.llm = build_llm(model_name) if model_name else None
        self._initialized = False

    def initialize(self, rebuild: Optional[bool] = None):
        """Load (or rebuild) the vector store index, once per instance.

        A no-op if already initialized. Marks the engine initialized only
        if an index was loaded, or a rebuild produced at least one chunk.

        Args:
            rebuild (bool | None): Force a rebuild from the knowledge base
                directory; defaults to `self.config.auto_rebuild` if
                omitted.
        """
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
        """Retrieve documents passing the configured similarity threshold.

        Uses similarity_search_with_score (not similarity_search) so the same
        relevance gate as query() applies here too - format_context() and
        format_combined_context() (used on every live ArgusBrain query) were
        previously bypassing the threshold entirely.

        Args:
            query (str): The search query text.
            k (int | None): Max results to consider before filtering;
                defaults to `self.config.retriever_k`.

        Returns:
            List[Document]: Documents whose similarity score is `<=` the
            configured `similarity_threshold` (lower is more similar).
        """
        self.initialize()
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return [doc for doc, score in results if score <= self.config.similarity_threshold]

    def retrieve_with_scores(self, query: str, k: Optional[int] = None) -> List[tuple]:
        """Like `retrieve()`, but returns every result with its raw score,
        unfiltered by the similarity threshold.

        Args:
            query (str): The search query text.
            k (int | None): Max results; defaults to
                `self.config.retriever_k`.

        Returns:
            List[tuple]: `(Document, score)` pairs, most similar first.
        """
        self.initialize()
        return self.vector_store.similarity_search_with_score(query, k=k)

    def augment(self, query: str, context_chunks: List[str]) -> str:
        """Synthesize an answer from retrieved context chunks via the configured LLM.

        Args:
            query (str): The original question.
            context_chunks (List[str]): Retrieved chunk texts to ground
                the answer in.

        Returns:
            str: The LLM's synthesized answer, or the raw joined
            `context_chunks` verbatim if no LLM was configured
            (`model_name` was omitted at construction).
        """
        context = "\n\n---\n\n".join(context_chunks)
        if self.llm is None:
            return context

        chain = RAG_PROMPT | self.llm | StrOutputParser()
        return chain.invoke({"context": context, "question": query})

    def query(self, query: str, k: Optional[int] = None) -> RAGResult:
        """Retrieve threshold-passing chunks and synthesize an answer from them.

        Args:
            query (str): The question to answer.
            k (int | None): Max results to consider; defaults to
                `self.config.retriever_k`.

        Returns:
            RAGResult: `answer`/`sources`/`chunks` reflect only the
            similarity-threshold-passing results (an explicit "No
            relevant information found" answer if none pass); `all_chunks`
            always holds every retrieved chunk regardless of threshold.
        """
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
        """Convenience wrapper returning just `query()`'s answer text.

        Args:
            query (str): The question to answer.
            k (int | None): Max results to consider; defaults to
                `self.config.retriever_k`.

        Returns:
            str: `self.query(query, k=k).answer`.
        """
        result = self.query(query, k=k)
        return result.answer

    def add_document(self, file_path: str) -> bool:
        """Load, chunk, and index a single new document into the vector store.

        Args:
            file_path (str): Path to the document to ingest.

        Returns:
            bool: True if at least one chunk was indexed; False if the
            file couldn't be loaded (unsupported extension, missing file,
            or empty) or produced zero chunks.
        """
        # DocumentProcessor.load_file() returns Optional[List[Document]] -
        # one input file can legitimately produce multiple Document chunks
        # (e.g. a markdown file split by H1/H2/H3 headers, a CSV split
        # row-by-row - see document_processor.py's structural chunking).
        # The previous `splitter.split_documents([doc])` wrapped this
        # already-a-list in a second list, so split_documents() (which
        # expects Iterable[Document]) iterated once and got the inner list
        # itself where it expected a Document, crashing on `.page_content`
        # - confirmed live via scripts/test_rag.py --smoke --no-llm.
        docs = self.processor.load_file(file_path)
        if not docs:
            return False

        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        self.initialize(rebuild=False)
        count = self.vector_store.build_index(chunks)
        return count > 0

    def rebuild_index(self):
        """Force a full rebuild: discard the current vector store and
        reprocess the whole knowledge base directory from scratch."""
        self._initialized = False
        self.vector_store = VectorStore(self.config)
        self.initialize(rebuild=True)

    def format_context(self, query: str, k: Optional[int] = None) -> str:
        """Retrieve threshold-passing chunks and format them as labeled context text.

        Args:
            query (str): The search query text.
            k (int | None): Max results to consider; defaults to
                `self.config.retriever_k`.

        Returns:
            str: Chunks joined with "---" separators, each prefixed with
            its `[Source: ...]` basename; "" if nothing passed the
            threshold.
        """
        results = self.retrieve(query, k=k)
        if not results:
            return ""

        return "\n\n---\n\n".join(
            f"[Source: {os.path.basename(d.metadata.get('source', 'unknown'))}]\n{d.page_content}"
            for d in results
        )

    def format_combined_context(self, query: str, blackboard_context: str = "", k: Optional[int] = None) -> str:
        """Combine static RAG context with live Blackboard findings into one labeled block.

        Args:
            query (str): The search query text, passed to `format_context`.
            blackboard_context (str): Live recon/finding text to append
                under its own "LIVE TARGET STATE" section; omitted
                entirely if empty.
            k (int | None): Max RAG results to consider; defaults to
                `self.config.retriever_k`.

        Returns:
            str: The RAG context section, the Blackboard section, both,
            or "" if both are empty.
        """
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
