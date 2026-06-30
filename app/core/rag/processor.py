from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
import os

class RAGDocumentChunk(BaseModel):
    """Schema for a RAG Document Chunk."""
    id: str = Field(description="Unique identifier for the chunk")
    page_content: str = Field(description="The actual text content")
    metadata: Dict[str, Any] = Field(description="Source file path, page number, etc.")

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def load_and_split(self, file_path: str) -> List[Document]:
        """Loads a document and splits it into chunks."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
            
        if file_path.endswith('.md'):
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            loader = TextLoader(file_path)
            
        docs = loader.load()
        chunks = self.text_splitter.split_documents(docs)
        
        # We return LangChain Documents directly since they are required by FAISS
        return chunks
