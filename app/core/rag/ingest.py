from rag_pipeline.ingestion_chunking import run_ingestion_and_chunking
from rag_pipeline.embedding_storage import save_to_chroma


def main():
    """
    Run the full RAG ingestion pipeline.
    """

    # 1. Load data and split it into chunks
    chunks = run_ingestion_and_chunking()

    if not chunks:
        print("[-] Pipeline aborted: No data to process.")
        return

    # 2. Save chunks into the vector database
    save_to_chroma(chunks)


if __name__ == "__main__":
    main()