# Contract: DocumentProcessor

**Module**: `app/core/rag/document_processor.py`

---

## Interface

```python
class DocumentProcessor:
    def load_from_directory(self, directory: Optional[str] = None) -> List[Document]: ...
    def load_file(self, file_path: str) -> Optional[List[Document]]: ...
    def split_documents(self, documents: List[Document]) -> List[Document]: ...
    def process_directory(self, directory: Optional[str] = None) -> List[Document]: ...
```

## Behaviour

| Condition | Result |
|-----------|--------|
| Directory exists with supported files | Returns `Document[]` — one per file/row/page |
| Directory missing | Returns `[]`, logs warning |
| Binary/unreadable file encountered | Skips file, logs warning, continues |
| Unsupported extension | Skips silently |
| Markdown files in `split_documents` | Uses `MarkdownHeaderTextSplitter` with H1/H2/H3 |
| Generic files in `split_documents` | Uses `RecursiveCharacterTextSplitter` (chunk_size, chunk_overlap) |

## Supported Extensions

`.txt`, `.md`, `.pdf`, `.json`, `.csv`, `.html`, `.yaml`, `.yml`, `.xml`

## Test Contract

- Test each file type separately (txt, md, pdf, csv, json, html)
- Test empty directory
- Test directory with only unsupported files
- Test binary file handling (e.g. `.png` or `.exe` in directory)
- Test `split_documents` with mixed md/generic input
- Test edge: single document, zero documents
