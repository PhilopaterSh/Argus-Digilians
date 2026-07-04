# DEPRECATED: This file is deprecated. Use app/core/rag/rag_engine.py instead.
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.core.rag.processor import DocumentProcessor
from app.core.rag.vectorstore import VectorStoreManager

class RAGEngine:
    def __init__(self, llm_model: str = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest", embed_model: str = "nomic-embed-text"):
        self.processor = DocumentProcessor()
        self.vector_manager = VectorStoreManager(model_name=embed_model)
        self.llm = Ollama(model=llm_model)
        
        # Define the prompt template for QA
        self.prompt = PromptTemplate.from_template(
            """You are a tactical assistant. Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know. Keep the answer concise.

Context: {context}

Question: {question}

Answer:"""
        )

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def ingest(self, file_path: str):
        """Linearly processes a document and indexes it."""
        chunks = self.processor.load_and_split(file_path)
        self.vector_manager.index_documents(chunks)
        return len(chunks)

    def query(self, question: str) -> str:
        """Executes a linear, deterministic RAG pipeline."""
        retriever = self.vector_manager.get_retriever()
        
        # Build the LangChain LCEL (LangChain Expression Language) pipeline
        rag_chain = (
            {"context": retriever | self.format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain.invoke(question)
