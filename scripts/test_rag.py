import argparse
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.rag.config import RAGConfig
from app.core.rag.rag_engine import RAGEngine

DEFAULT_SAMPLE = """Argus RAG smoke test.
The knowledge base documents a local recon workflow.
FAISS is used for vector retrieval.
Ollama embeddings are preferred for offline use.
"""


def _write_sample_doc() -> str:
    tmp_dir = Path(tempfile.mkdtemp(prefix='argus_rag_smoke_'))
    doc_path = tmp_dir / 'sample.md'
    doc_path.write_text(DEFAULT_SAMPLE, encoding='utf-8')
    return str(doc_path)


def main():
    parser = argparse.ArgumentParser(description='Test linear RAG pipeline')
    parser.add_argument('--ingest', help='Path to document to ingest')
    parser.add_argument('--query', help='Query to run against the ingested document')
    parser.add_argument('--no-llm', action='store_true', help='Run in mock/no-LLM mode to check chunk retrieval only')
    parser.add_argument('--smoke', action='store_true', help='Run a self-contained smoke test with a temporary document')
    args = parser.parse_args()

    ingest_path = args.ingest
    query_text = args.query

    if args.smoke or not ingest_path or not query_text:
        ingest_path = _write_sample_doc()
        query_text = query_text or 'What does the knowledge base say about FAISS and Ollama?'
        print(f'Running smoke test with temporary document: {ingest_path}')

    if not os.path.exists(ingest_path):
        print(f'Error: Document {ingest_path} not found.')
        return 1

    print('Initializing RAG Engine...')
    config = RAGConfig(
        embedding_model='nomic-embed-text',
        auto_rebuild=False,
    )

    llm_model = None if args.no_llm else 'WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest'
    engine = RAGEngine(config=config, model_name=llm_model)

    print(f'Ingesting document: {ingest_path}')
    success = engine.add_document(ingest_path)
    if success:
        print('Document processed and ingested successfully.')
    else:
        print('Failed to ingest document or document is empty.')
        return 1

    print(f'\nQuerying: {query_text}')
    print('-' * 50)

    if args.no_llm:
        print('Retrieving relevant chunks (without LLM):')
        chunks = engine.retrieve(query_text)
        for i, chunk in enumerate(chunks):
            print(f'Chunk {i + 1} [Source: {chunk.metadata.get("source")}]:')
            print(chunk.page_content)
            print('-' * 30)
    else:
        try:
            result = engine.query(query_text)
            print(f'Response:\n{result.answer}')
            print('\nSources:')
            for src in result.sources:
                print(f"- {os.path.basename(src['metadata'].get('source', 'unknown'))} (Score: {src['score']:.4f})")
        except Exception as e:
            print(f'Failed to query LLM (Is Ollama running?): {e}')
            print('\nRetrieving chunks as fallback:')
            chunks = engine.retrieve(query_text)
            for i, chunk in enumerate(chunks):
                print(f'Chunk {i + 1}: {chunk.page_content}')

    print('-' * 50)
    print('Linear RAG execution completed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
