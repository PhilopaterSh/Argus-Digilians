# Implementation Plan: RAG Pipeline Audit & Hardening

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-29 | **Spec**: `specs/004-rag-pipeline/spec.md`

**Input**: Feature specification from `specs/004-rag-pipeline/spec.md`

---

## Summary

Harden the existing RAG subsystem (`app/core/rag/`, built in Phase 001) with comprehensive unit tests, embedding fallback verification, FAISS index integrity checks, and proper error handling across all 6 modules. Ensure alignment with `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` §5.1 RAG Subsystem.

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: langchain-core, faiss-cpu, sentence-transformers, pypdf (all already in `Argus_venv` via `requirements_embedded.txt`)

**Storage**: FAISS index persisted to `app/core/rag/store/`; knowledge base at `knowledge_base/`

**Testing**: pytest (already installed in venv via Phase 003 test setup)

**Target Platform**: Windows 10/11 + WSL2 (Kali) — RAG runs on Windows host only

**Project Type**: AI RAG subsystem (library module within larger framework)

**Performance Goals**: similarity_search returns in under 500ms for 10K chunks

**Constraints**: System must not be required for basic operation — RAG is a performance enhancement, not a hard dependency

**Scale/Scope**: 6 existing Python modules, ~800 LOC, 5 supported document formats

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Admin-First Elevation | ✅ Not Applicable | RAG is a pure Python library; no OS changes |
| II. Single-Source Installer | ✅ Not Applicable | No installer changes needed |
| III. Idempotent & Test-Gated | ✅ Compliant | All operations are read-only or safely rebuildable |
| IV. Platform-Boundary Clarity | ✅ Compliant | Runs on Windows host only; no WSL dependency |
| V. Observability & Logging | ⚠️ Needs Work | Add structured logging to all RAG modules |
| VI. English-Only Documentation | ✅ Compliant | Existing docs in English |

**Gate Decision**: PASS — no violations requiring Complexity Tracking.

---

## Project Structure

### Documentation (this feature)

```text
specs/004-rag-pipeline/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: embedding model comparison
├── data-model.md        # Phase 1: RAG data flow model
├── quickstart.md        # Phase 1: validation guide
└── tasks.md             # Phase 2: actionable tasks (created by /speckit.tasks)
```

### Source Code (repository root)

```text
app/core/rag/
├── __init__.py
├── config.py
├── embeddings.py
├── document_processor.py
├── vector_store.py
└── rag_engine.py

knowledge_base/
├── .gitkeep
└── argus_security_knowledge.md

app/core/rag/store/
└── index.faiss / index.pkl

tests/
└── test_rag/
    ├── test_embeddings.py
    ├── test_document_processor.py
    ├── test_vector_store.py
    └── test_rag_engine.py
```

**Structure Decision**: Keep existing flat module layout. Tests go in `tests/test_rag/` following the pattern established in Phase 003 (`tests/test_memory.py`).

---

## Complexity Tracking

No constitution violations — Complexity Tracking table is not required.

---

## Alignment with Architecture Vision

This feature directly implements the **RAG Subsystem** described in `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`:

| Architecture Component | Implementation |
|------------------------|----------------|
| EmbeddingFactory (§5.1) | `app/core/rag/embeddings.py` — 3-tier fallback |
| DocumentProcessor (§5.2) | `app/core/rag/document_processor.py` — structural chunking |
| VectorStore (§5.1) | `app/core/rag/vector_store.py` — FAISS |
| RAGEngine (§5.1) | `app/core/rag/rag_engine.py` — query + context fusion |
