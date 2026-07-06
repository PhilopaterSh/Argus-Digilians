# Tasks: Spec Consolidation & Architecture Reconciliation

**Input**: `specs/012-spec-reconciliation/spec.md`, `specs/012-spec-reconciliation/plan.md`

**Goal**: one consistent, executable, maintainable spec set. Documentation only.

---

## Phase 0 — Numbering

- [x] T001 Rename `specs/003-langgraph-workflow/` → `specs/013-langgraph-workflow/` (resolve duplicate `003`).
- [x] T002 Fix internal self-references (spec/plan/tasks headers and paths) in `013`.

## Phase 1 — Canonical authority

- [x] T003 Author `012` spec (naming, embedding §3, agent §4, parsing §5, testing §6, CI/CD §7).
- [x] T004 Author `012` plan (source-of-truth map, supersession map, phases).
- [x] T005 Author `012` tasks (this file).

## Phase 2 — Supersession headers

- [x] T006 Add "Partially Superseded By" header to `013` spec/plan/tasks.
- [x] T007 Add "Refined By 012 §3" header to `001` spec.
- [x] T008 Add "Refined By 012 §3" header to `004` spec.
- [x] T009 Update `005` spec Input (brain_v2 consolidated per `012` §2.2).
- [x] T010 Add canonical/name-alignment header to `010` spec + plan.

## Phase 3 — Embedding manifest design

- [x] T011 Rewrite `001` FR-005..007 to one-embedder-per-index + manifest + rebuild-on-change (build-time-only fallback; RAG-disabled on mismatch).
- [x] T012 Update `001` plan Complexity Tracking + Key Design Decisions (manifest).
- [x] T013 Update `004` spec FR-001/FR-002 to reference `manifest.json` as the integrity artifact.

## Phase 4 — Naming / chunking / agent alignment

- [x] T014 Align `010` plan module names (`processor→document_processor`, `vectorstore→vector_store`, `engine→rag_engine`; add `config.py`, `embeddings.py`).
- [x] T015 Align `010` tasks module names to canonical.
- [x] T016 Note structural chunking as canonical in `010` (RecursiveCharacterTextSplitter = fallback).

## Phase 5 — Architecture document

- [x] T017 Update ADR-9 (embedding manifest) in `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`.
- [x] T018 Add ADR-13 (structured-output parsing), ADR-14 (canonical naming + single Brain), ADR-15 (canonical agent topology), ADR-16 (unified port).
- [x] T019 Standardize Python `3.12`, port `12199`, single `ArgusBrain`, tool count `17` in the architecture doc.

## Phase 6 — Future (out of scope for this documentation pass)

- [ ] T020 Author a `ci-cd` plan doc/YAML implementing `012` §7.
- [ ] T021 Translate/retire Arabic `converge.md` files for English-only compliance (constitution VI).
- [ ] T022 Implement `010` against the reconciled design; migrate `app/core/workflow/` into `app/core/agent/`.

## Phase 7 — Convergence gap register (code vs canonical; discovered 2026-07-05)

Code inspection found physical drift: the repo contains BOTH canonical and superseded
files side by side. These tasks close the code↔`012` gap (implementation work; specs
already reconciled). Add-only — no completed task is recreated.

- [x] T024 `config.yaml` `streamlit.port` corrected `8199` → `12199` (ADR-16). ✅ Done.
- [~] T025 Remove duplicate RAG modules (`processor.py`, `vectorstore.py`, `engine.py`); keep `document_processor.py` / `vector_store.py` / `rag_engine.py` (`012` §2.1). **PARTIAL:** confirmed these are dead forwarders (no importers); operationalized their deprecation with runtime `DeprecationWarning`. **Physical deletion BLOCKED** in current environment (mount returns "Operation not permitted" on unlink) — remove in a normal dev checkout.
- [ ] T026 Consolidate Brain: merge `app/core/agent/brain_v2.py` (`ArgusBrainV2`) + `app/core/brain.py` (`ArgusBrain`) into a single `app/core/agent/brain.py`; delete the shadow files (`012` §2.2, ADR-14).
- [ ] T027 Consolidate factory: merge `app/core/agent/agent_factory_v2.py` + `app/core/agent_factory.py` into `app/core/agent/agent_factory.py`; delete shadows.
- [ ] T028 Migrate reusable parts of `app/core/workflow/` (parser, hooks, prompts, capability probe) into `app/core/agent/`, then remove `app/core/workflow/` (`013` retained-scope; `012` §2.2).
- [ ] T029 Implement `app/core/rag/store/manifest.json` (embedder name/provider/dimension + knowledge_base hash + schema_version) in `vector_store.py`; wire deterministic rebuild in `rag_engine.py` (`012` §3, ADR-9).
- [ ] T030 Implement Ollama `format=json` structured decoding as primary Action path; keep regex parser as fallback (`012` §5, ADR-13).
- [x] T031 `get_port.py` rewritten with a fail-safe default of `12199` (`012` §2.6); ✅ Done and validated (normal → 12199, missing-config → 12199).

## Phase 8 — Newly discovered (2026-07-05): non-ASCII / mixed-language in first-party code

Constitution VI requires ASCII-safe console/log output and no mixed-language files.
A scan of `app/`, `scripts/`, `tests/` found 26 files with non-ASCII bytes. Classified:
mostly emoji/symbols in log/report strings (cosmetic, valid UTF-8, runs today), plus
**Arabic text in 3 GUI files** (`app/GUI/app.py`, `gui_app.py`, `gui_root.py` — two are
already deprecated per `009`/`011`). NOT fixed in this environment: mass-editing working
/ deprecated code and altering output strings cannot be safely validated here (no test
runtime; deprecated files pending removal). Requires a dev environment with the test suite.

- [x] T032 Removed all non-ASCII from first-party code (24 files + `test_cd.bat`): emoji/box-drawing/arrows/dashes/Kali-prompt symbols -> ASCII equivalents; `config.yaml` `§` -> `sec`. **0 non-ASCII bytes** remain in `app/`, `scripts/`, `tests/` (`.py/.bat/.ps1/.sh`). Intentional Unicode round-trip data in `tests/test_memory.py` preserved as `\uXXXX` escapes (identical runtime values). All cleaned files `py_compile` OK. ✅ Done 2026-07-05.
- [x] T033 Arabic converted to English: the 3 `# تصميم بسيط واحترافي` comments in `app/GUI/{app,gui_app,gui_root}.py` -> `# Simple, professional design`. Corrupted UTF-16 `tests/test_cd.bat` reconstructed as ASCII. ✅ Done 2026-07-05. (Deprecated GUIs cleaned in place; full removal still tracked with `011`.)

## Out of Scope (explicit)

- [ ] T023 Any authorization / allow-list / human-in-the-loop / target-validation mechanism — intentionally excluded from this effort.
