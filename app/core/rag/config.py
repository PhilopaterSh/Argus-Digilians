import os
from dotenv import load_dotenv

# Load environment variables from the .env file, if needed
load_dotenv()

# --- Local Server Settings (Ollama) ---
# Get the URL and port from the .env file, or use the default value if not provided
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Define the new local models
LLM_MODEL = os.getenv("OLLAMA_MODEL", "whiterabbit")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# --- Project Folders ---
DATA_DIR = "./data"

# Note: Whether you are using ChromaDB or FAISS, keep the database path as you prefer
CHROMA_DB_DIR = "./chroma_db"

# --- Text Splitting Settings ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Local Validation ---
# Removed the GOOGLE_API_KEY requirement and replaced it with a check/confirmation for the local server setup
print(f"[+] Local Config Loaded: Using LLM ({LLM_MODEL}) and Embeddings ({EMBEDDING_MODEL}) via {OLLAMA_BASE_URL}")