from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
import os

class VectorStoreManager:
    def __init__(self, model_name: str = "nomic-embed-text"):
        # We assume Ollama is running locally and has the embedding model pulled
        self.embeddings = OllamaEmbeddings(model=model_name)
        self.vector_store = None

    def index_documents(self, documents: List[Document]) -> FAISS:
        """Indexes a list of documents using FAISS."""
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        return self.vector_store

    def save_local(self, folder_path: str):
        """Saves the FAISS index to disk."""
        if self.vector_store:
            self.vector_store.save_local(folder_path)

    def load_local(self, folder_path: str):
        """Loads a FAISS index from disk."""
        if os.path.exists(folder_path):
            # allow_dangerous_deserialization is needed for loading FAISS indexes in recent Langchain versions
            self.vector_store = FAISS.load_local(folder_path, self.embeddings, allow_dangerous_deserialization=True)

    def get_retriever(self, search_kwargs: dict = None):
        """Returns a retriever interface from the vector store."""
        if not self.vector_store:
            raise ValueError("Vector store has not been initialized or loaded.")
        kwargs = search_kwargs or {"k": 4}
        return self.vector_store.as_retriever(search_kwargs=kwargs)
