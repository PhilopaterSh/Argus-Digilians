# Tasks: RAG Pipeline Audit & Hardening

**Input**: Design documents from `specs/004-rag-pipeline/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Foundation & Audit

**Purpose**: Inventory the existing RAG subsystem before hardening.

- [x] T001 Audit existing `app/core/rag/embeddings.py` — verify 3-tier fallback (Ollama nomic-embed-text → HuggingFace all-MiniLM-L6-v2)
- [x] T002 Audit existing `app/core/rag/document_processor.py` — verify structural chunking + 5 format support (.md, .txt, .json, .csv, .pdf)
- [x] T003 Audit existing `app/core/rag/vector_store.py` — verify FAISS persistence to `app/core/rag/store/`
- [x] T004 Audit existing `app/core/rag/rag_engine.py` — verify query + context fusion + graceful missing-index handling
- [x] T005 Audit existing `app/core/rag/config.py` — verify central configuration

---

## Phase 2: US1 — Reliable RAG Queries (Priority: P1)

**Goal**: Embedding fallback works under failure, queries never crash the host.

**Independent Test**: Stop Ollama → RAG query returns HuggingFace-backed results, no exception.

### Implementation for User Story 1

- [ ] T006 [US1] Add structured logging to `embeddings.py` (which tier was used, fallback events)
- [ ] T007 [US1] Add explicit type hints + error handling to all 6 RAG modules (FR-005)
- [ ] T008 [US1] Harden `rag_engine.py`: missing index returns empty context, not an exception (FR-003)
- [ ] T009 [US1] Harden `document_processor.py`: binary/unreadable files skipped with WARN, not crash (FR-004)

---

## Phase 3: US2 — FAISS Index Integrity (Priority: P1)

**Goal**: Detect a stale/corrupt index automatically.

**Independent Test**: Tamper with `store/index.faiss` → system detects mismatch via checksum.

### Implementation for User Story 2

- [ ] T010 [US2] Add checksum/hash file (`store/index.sha256`) alongside FAISS index (FR-002)
- [ ] T011 [US2] Add `verify_index()` method to `vector_store.py` that recomputes hash and compares
- [ ] T012 [US2] Trigger auto-rebuild on checksum mismatch (WARN + rebuild from knowledge_base/)

---

## Phase 4: US3 — Test Coverage (Priority: P2)

**Goal**: Comprehensive unit tests for all RAG modules.

**Independent Test**: `pytest tests/test_rag/ -v` passes.

### Implementation for User Story 3

- [ ] T013 [P] [US3] Create `tests/test_rag/` directory with `__init__.py`
- [ ] T014 [P] [US3] Write `tests/test_rag/test_embeddings.py` — test each fallback tier with mocked models (FR-001)
- [ ] T015 [P] [US3] Write `tests/test_rag/test_document_processor.py` — test 5 formats + binary-file skip
- [ ] T016 [P] [US3] Write `tests/test_rag/test_vector_store.py` — test add/search/checksum verification
- [ ] T017 [P] [US3] Write `tests/test_rag/test_rag_engine.py` — test query + missing-index graceful handling

---

## Phase 5: Polish & Performance

**Purpose**: Performance goal (<500ms for 10K chunks) + documentation alignment.

- [ ] T018 [P] Benchmark `similarity_search` against a 10K-chunk fixture
- [ ] T019 [P] Run full test suite: `pytest tests/test_rag/ -v`
- [ ] T020 [P] Validate quickstart.md steps manually

---

## Phase 6: Commit Strategy (Cross-Cutting)

- [x] T000 Follow commit-per-phase strategy (per `Plan.md` §4)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundation (Phase 1)**: No dependencies — audit only
- **US1 (Phase 2)**: Depends on Foundation
- **US2 (Phase 3)**: Depends on Foundation
- **US3 (Phase 4)**: Depends on US1 + US2
- **Polish (Phase 5)**: Depends on all stories

### Parallel Opportunities

- T014, T015, T016, T017 (test files) all touch independent files → parallel [P]
- T018, T019, T020 (polish) → parallel [P]

### Execution Order

1. T001 → T002 → T003 → T004 → T005 (Phase 1: audit)
2. T006 → T007 → T008 → T009 (Phase 2: US1)
3. T010 → T011 → T012 (Phase 3: US2)
4. T013 → T014 [P] + T015 [P] + T016 [P] + T017 [P] (Phase 4: US3)
5. T018 [P] + T019 [P] + T020 [P] (Phase 5: polish)

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Foundation & Audit | ✅ Complete | All 6 modules exist and audited |
| Phase 2: US1 Reliable Queries | ⏳ Pending | Logging + hardening not yet added |
| Phase 3: US2 Index Integrity | ⏳ Pending | Checksum verification not yet added |
| Phase 4: US3 Test Coverage | ⏳ Pending | `tests/test_rag/` does not exist yet |
| Phase 5: Polish | ⏳ Pending | Blocked on Phases 2-4 |

> **Note**: Phase 001 built the RAG subsystem. This feature (004) hardens it with
> tests, integrity checks, and error handling — that work is **not yet started**.
