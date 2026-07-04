import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.rag.rag_engine import RAGEngine
from app.core.rag.config import RAGConfig

def main():
    parser = argparse.ArgumentParser(description="Test linear RAG pipeline")
    parser.add_argument("--ingest", help="Path to document to ingest", required=True)
    parser.add_argument("--query", help="Query to run against the ingested document", required=True)
    parser.add_argument("--no-llm", action="store_true", help="Run in mock/no-LLM mode to check chunk retrieval only")
    args = parser.parse_args()

    if not os.path.exists(args.ingest):
        print(f"Error: Document {args.ingest} not found.")
        return

    print(f"Initializing RAG Engine...")
    # Using config to match local environment defaults
    config = RAGConfig(
        embedding_model="nomic-embed-text",
        auto_rebuild=False
    )
    
    # If no-llm is requested, we don't need to instantiate the LLM
    llm_model = None if args.no_llm else "llama2"
    engine = RAGEngine(config=config, model_name=llm_model)

    print(f"Ingesting document: {args.ingest}")
    success = engine.add_document(args.ingest)
    if success:
        print("Document processed and ingested successfully.")
    else:
        print("Failed to ingest document or document is empty.")
        return

    print(f"\nQuerying: {args.query}")
    print("-" * 50)
    
    if args.no_llm:
        print("Retrieving relevant chunks (without LLM):")
        chunks = engine.retrieve(args.query)
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1} [Source: {chunk.metadata.get('source')}]:")
            print(chunk.page_content)
            print("-" * 30)
    else:
        # Check if Ollama model is available, otherwise show warning or run
        try:
            result = engine.query(args.query)
            print(f"Response:\n{result.answer}")
            print("\nSources:")
            for src in result.sources:
                print(f"- {os.path.basename(src['metadata'].get('source', 'unknown'))} (Score: {src['score']:.4f})")
        except Exception as e:
            print(f"Failed to query LLM (Is Ollama running?): {e}")
            print("\nRetrieving chunks as fallback:")
            chunks = engine.retrieve(args.query)
            for i, chunk in enumerate(chunks):
                print(f"Chunk {i+1}: {chunk.page_content}")
                
    print("-" * 50)
    print("Linear RAG execution completed.")

if __name__ == "__main__":
    main()

