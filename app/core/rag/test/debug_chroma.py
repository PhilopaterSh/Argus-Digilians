import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import CHROMA_DB_DIR, EMBEDDING_MODEL, OLLAMA_BASE_URL


embeddings = OllamaEmbeddings(
    model=EMBEDDING_MODEL,
    base_url=OLLAMA_BASE_URL
)

vector_db = Chroma(
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embeddings
)

print("Chroma path:", CHROMA_DB_DIR)
print("Collection count:", vector_db._collection.count())