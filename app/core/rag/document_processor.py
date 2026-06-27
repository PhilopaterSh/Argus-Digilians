import os
import csv
import json
import io
from typing import List, Optional
from langchain_core.documents import Document
from app.core.rag.config import RAGConfig


class DocumentProcessor:
    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".json", ".csv", ".html", ".yaml", ".yml", ".xml"}

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()

    def load_from_directory(self, directory: Optional[str] = None) -> List[Document]:
        target_dir = directory or self.config.knowledge_base_dir
        if not os.path.isdir(target_dir):
            print(f"[RAG] Knowledge base directory not found: {target_dir}")
            return []

        documents = []
        for root, _, files in os.walk(target_dir):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue
                fpath = os.path.join(root, fname)
                try:
                    docs = self._load_single(fpath, ext)
                    documents.extend(docs)
                except Exception as e:
                    print(f"[RAG] Error loading {fpath}: {e}")

        print(f"[RAG] Loaded {len(documents)} documents from {target_dir}")
        return documents

    def load_file(self, file_path: str) -> Optional[List[Document]]:
        if not os.path.isfile(file_path):
            return None
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return None
        return self._load_single(file_path, ext)

    def _load_single(self, fpath: str, ext: str) -> List[Document]:
        if ext == ".csv":
            return self._load_csv(fpath)
        elif ext == ".json":
            return self._load_json(fpath)
        elif ext == ".pdf":
            return self._load_pdf(fpath)
        else:
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(fpath)
            return loader.load()

    def _load_csv(self, fpath: str) -> List[Document]:
        docs = []
        with open(fpath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                content = "\n".join(f"{k}: {v}" for k, v in row.items() if v)
                doc = Document(
                    page_content=content,
                    metadata={"source": fpath, "row": i + 1},
                )
                docs.append(doc)
        print(f"[RAG] CSV '{os.path.basename(fpath)}': {len(docs)} rows")
        return docs

    def _load_json(self, fpath: str) -> List[Document]:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            docs = []
            for i, item in enumerate(data):
                content = json.dumps(item, ensure_ascii=False, indent=2)
                doc = Document(
                    page_content=content,
                    metadata={"source": fpath, "index": i},
                )
                docs.append(doc)
            print(f"[RAG] JSON list '{os.path.basename(fpath)}': {len(docs)} items")
            return docs

        else:
            content = json.dumps(data, ensure_ascii=False, indent=2)
            from langchain_text_splitters import RecursiveJsonSplitter
            splitter = RecursiveJsonSplitter(max_doc_size=self.config.chunk_size)
            texts = splitter.split_json(json.dumps(data, ensure_ascii=False))
            docs = [
                Document(page_content=t, metadata={"source": fpath})
                for t in texts
            ]
            print(f"[RAG] JSON object '{os.path.basename(fpath)}': {len(docs)} chunks")
            return docs

    def _load_pdf(self, fpath: str) -> List[Document]:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(fpath)
        docs = loader.load()
        print(f"[RAG] PDF '{os.path.basename(fpath)}': {len(docs)} pages")
        return docs

    def split_documents(self, documents: List[Document]) -> List[Document]:
        if not documents:
            return []

        md_texts = []
        generic_texts = []

        for doc in documents:
            src = doc.metadata.get("source", "")
            ext = os.path.splitext(src)[1].lower()
            if ext == ".md":
                md_texts.append(doc)
            else:
                generic_texts.append(doc)

        chunks = []

        if md_texts:
            from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
            headers_to_split_on = [
                ("#", "Header1"),
                ("##", "Header2"),
                ("###", "Header3"),
            ]
            md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            for doc in md_texts:
                try:
                    header_splits = md_splitter.split_text(doc.page_content)
                    for hd in header_splits:
                        hd.metadata["source"] = doc.metadata.get("source", "")
                    chunks.extend(header_splits)
                except Exception:
                    generic_texts.append(doc)

        if generic_texts:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                length_function=len,
            )
            chunks.extend(splitter.split_documents(generic_texts))

        print(f"[RAG] Structural split: {len(chunks)} chunks from {len(documents)} docs")
        return chunks

    def process_directory(self, directory: Optional[str] = None) -> List[Document]:
        docs = self.load_from_directory(directory)
        return self.split_documents(docs)
