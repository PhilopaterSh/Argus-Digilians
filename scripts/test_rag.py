import argparse
import os
from app.core.rag.engine import RAGEngine

def main():
    parser = argparse.ArgumentParser(description="Test linear RAG pipeline")
    parser.add_argument("--ingest", help="Path to document to ingest", required=True)
    parser.add_argument("--query", help="Query to run against the ingested document", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.ingest):
        print(f"Error: Document {args.ingest} not found.")
        return

    print(f"Initializing RAG Engine...")
    engine = RAGEngine(llm_model="llama2", embed_model="nomic-embed-text") # Using simpler local models for test

    print(f"Ingesting document: {args.ingest}")
    num_chunks = engine.ingest(args.ingest)
    print(f"Document processed into {num_chunks} chunks.")

    print(f"\nQuerying: {args.query}")
    print("-" * 50)
    response = engine.query(args.query)
    print(f"Response:\n{response}")
    print("-" * 50)
    print("Linear RAG execution completed.")

if __name__ == "__main__":
    main()
