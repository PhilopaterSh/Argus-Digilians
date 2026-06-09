import os
import shutil

# 1. Replace the Google Embedding class with the local class from langchain_ollama
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

# Import the local server URL variable that we added in the config file
from config import CHROMA_DB_DIR, EMBEDDING_MODEL, OLLAMA_BASE_URL


def save_to_chroma(chunks):
    """
    Clean the old database, generate local embeddings for the chunks,
    and store them in ChromaDB.
    """

    # Stop if there are no chunks
    if not chunks:
        print("[-] Error: No chunks received. Cannot create vector database.")
        return None

    # Delete the old Chroma database if it exists to prevent duplicate data
    if os.path.exists(CHROMA_DB_DIR):
        print(f"[!] Clearing old database in '{CHROMA_DB_DIR}' to prevent duplicates...")
        shutil.rmtree(CHROMA_DB_DIR)

    # Update the print message to reflect the switch to local embeddings
    print(f"[+] Phase 2: Generating local '{EMBEDDING_MODEL}' embeddings and saving to '{CHROMA_DB_DIR}'...")

    # 2. Create the local Embedding module and point it to the Ollama server port
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL
    )

    # Create and save the Chroma vector database
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    print(f"[✔] SUCCESS: Vector database is ready and stored in '{CHROMA_DB_DIR}'")

    return vector_db