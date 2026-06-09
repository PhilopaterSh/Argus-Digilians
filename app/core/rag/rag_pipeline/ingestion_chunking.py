import os
import json

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP

def load_json_files(directory=DATA_DIR):
    """
    Load all JSON files from a directory and convert them into LangChain Documents.
    """
    documents = []

    if not os.path.exists(directory):
        print(f"[-] Error: Directory '{directory}' does not exist.")
        return documents

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)

            with open(filepath, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)

                    text_content = json.dumps(
                        data,
                        indent=2,
                        ensure_ascii=False
                    )

                    document = Document(
                        page_content=text_content,
                        metadata={"source": filename}
                    )

                    documents.append(document)

                except json.JSONDecodeError:
                    print(f"[-] Error: Could not parse {filename}. Invalid JSON format.")

    return documents

def split_documents(documents):
    """
    Split documents into smaller text chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    chunks = text_splitter.split_documents(documents)

    return chunks

def run_ingestion_and_chunking():
    """
    Load JSON files and split them into chunks.
    """
    print(f"\n[+] Phase 1: Loading JSON files from '{DATA_DIR}'...")

    raw_documents = load_json_files(DATA_DIR)

    if not raw_documents:
        print("[-] Error: No JSON files found in the data folder.")
        return []

    print(f"[!] Successfully loaded {len(raw_documents)} JSON files.")
    print(f"[+] Phase 1: Splitting text into chunks. Chunk size: {CHUNK_SIZE}...")

    chunks = split_documents(raw_documents)

    print(f"[!] Created {len(chunks)} text chunks.")

    return chunks