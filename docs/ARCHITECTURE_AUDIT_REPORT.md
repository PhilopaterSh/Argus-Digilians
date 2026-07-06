# Architecture Audit Report - Argus Security Framework

**Date**: 2026-07-05 | **Canonical reference**: `specs/012-spec-reconciliation`
**Scope**: full repository (specs, code, docs, config, CI, automation)

> Environment note: this audit was produced in a sandbox where (a) file deletion is
> blocked and (b) the runtime (langchain/faiss/Ollama, Python 3.12) is unavailable.
> Deletions and behavioral refactors are therefore specified as an executable
> **Cleanup Manifest** (section 8) rather than applied in place. All *safe, verifiable*
> changes have been applied.

---

## 1. Area Reviewed: Repository root layout

### Problems found
- **P0 - Nested self-duplicate**: `Argus-Digilians-fix-copy-setup-to-scripts/` is a full
  1.6 GB copy of the entire repository (its own `.git`, `Argus_venv`, `app`, `specs`, `docs`).
  It is not git-tracked at the root - pure clutter and a source of confusion/drift.
- **P1 - Documentation sprawl**: 22 loose files at root, including 9 ad-hoc `*.txt` "fix"
  notes and several one-off `*_FIX.md` / `*_REPORT.md` files
  (`JSON_PARSING_FIX.md`, `PARSING_ERROR_FIX.md`, `TESTING_JSON_FIX.md`,
  `REACT_FORMAT_ERROR_FIX.txt`, `RADICAL_FIX_SIMPLE_CHAIN_FALLBACK.txt`, etc.).
- **P2 - Stray directory**: `Plan md/` (folder name contains a space) holding a single `Plan.md`.
- **P2 - Loose root Python**: `check_integration.py` and `test_parsing_fix.py` live at the root
  instead of `tests/` or `scripts/`.

### Improvements applied
- Hardened `.gitignore`: added `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`,
  `htmlcov/`, `node_modules/`, `.opencode/node_modules/`, and the nested self-duplicate path.
  Prevents 1.6 GB of clutter and all tool caches from being committed.

### Files modified
- `.gitignore`

### Compatibility
No behavior change - `.gitignore` only affects what git tracks; no source or config touched.

---

## 2. Area Reviewed: GUI subsystem (`app/GUI/`)

### Problems found
- **P0 - 8 overlapping entrypoints**: `app.py`, `argus_gui.py`, `argus_studio.py`,
  `desktop_gui.py`, `gui_app.py`, `gui_main.py`, `gui_root.py`, `studio.py`. The canonical
  primary UI per `012` section 2.5 / `011` is a single `app/GUI/dashboard.py`, which does not
  yet exist; `argus_studio.py` appears to be the closest current implementation.
- **P1 - Naming drift**: `011` specifies `dashboard.py`; the code uses `argus_studio.py`.

### Improvements applied (this environment)
- None applied in place (consolidation requires running the Streamlit app to verify parity;
  deletion is blocked). Captured as Cleanup Manifest C3.

### Recommendation
Adopt one canonical `app/GUI/dashboard.py` (rename/align `argus_studio.py`), keep
`desktop_gui.py` as the optional Tkinter fallback (per `012` 2.5), and reduce the remaining six
to thin deprecation shims, then remove (C3).

---

## 3. Area Reviewed: Agent / Brain core (`app/core/`)

### Problems found (already tracked in `012` T026-T028)
- `app/core/brain.py` (`ArgusBrain`) and `app/core/agent/brain_v2.py` (`ArgusBrainV2`) - two brains.
- `app/core/agent_factory.py` and `app/core/agent/agent_factory_v2.py` - two factories.
- `app/core/workflow/` (013 generic ReAct) and `app/core/agent/graph.py` (010 node graph) -
  two agent designs.

### Improvements applied
- None in place - behavioral merge requires the test suite (unavailable here). Fully specified
  in `012` tasks T026-T028 and Cleanup Manifest C4. Import graph already proven:
  `brain_v2`/`agent_factory_v2`/`workflow` are imported only by tests.

### Compatibility
Deferred deliberately; doing this blind would break `tests/test_registry/*` and
`tests/test_langgraph_workflow.py`.

---

## 4. Area Reviewed: RAG subsystem (`app/core/rag/`)

### Problems found
- Superseded forwarders `processor.py` / `vectorstore.py` / `engine.py` still present
  (zero importers; deprecation warnings added earlier this session).

### Improvements applied (earlier phases, verified)
- Canonical naming enforced; forwarders now emit `DeprecationWarning`.
- `manifest.py` (one embedder per index, `012` section 3) implemented + 10 passing unit tests.

### Status
Deletion of the three forwarders is blocked by the environment (Cleanup Manifest C2).

---

## 5. Area Reviewed: Spec-Kit artifact completeness (`specs/`)

### Problems found
- Missing artifacts:
  - `002-consolidated-installer/`: no `research.md`, `data-model.md`, `quickstart.md`
  - `003-sqlite-blackboard/`: no `research.md`, `data-model.md`, `quickstart.md`
  - `013-langgraph-workflow/`: no `research.md`, `data-model.md`, `quickstart.md`
    (lower priority - `013` is Partially Superseded)

### Improvements applied
- `012` artifact set completed earlier (spec/plan/research/data-model/quickstart/tasks +
  github-issues-plan). Numbering collision resolved (`003` -> `013`). Supersession headers added
  to `001`/`004`/`009`/`010`/`013`. Statuses corrected on `003-sqlite`/`005`/`006`/`007`/`008`.

### Recommendation
Author the 6 missing artifacts for `002` and `003-sqlite` from their existing spec/plan (no new
decisions required). Tracked as Cleanup Manifest C5.

---

## 6. Area Reviewed: Documentation set (`docs/` + root)

### Problems found
- **Duplicate/overlapping architecture docs**: `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` (canonical),
  `docs/ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md` (archived - acceptable), plus root
  `Argus_Master_Documentation.md`, `IMPLEMENTATION_GUIDE.md`, `INSTALLATION_GUIDE.md`,
  `INSTALL*.md`, and multiple `*_FIX.md`/`*_REPORT.md` that overlap installer/parsing content
  already owned by specs `002`/`013`.
- **Single source of truth**: architecture -> `ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`; decisions ->
  its ADR section; consolidation -> `012`. The root `*_FIX`/`*_REPORT` notes duplicate these.

### Improvements applied
- Architecture doc already reconciled to canonical (ADR-9/13/14/15/16, port 12199, Python 3.12,
  single Brain, embedding manifest) in earlier phases.

### Recommendation
Move transient fix-notes to `docs/history/` (or delete) and point any surviving guide at the
canonical architecture doc. Tracked as Cleanup Manifest C6.

---

## 7. Feature -> Implementation Traceability Matrix

| Feature | Status | Primary implementation | Tests | Notes |
|---------|--------|------------------------|-------|-------|
| 001 RAG integration | Implemented (Refined by 012 s3) | `app/core/rag/*` | via 004 | canonical names |
| 002 Installer | Draft | `scripts/ARGUS_INSTALLER.ps1` | `tests/pester/` | missing 3 artifacts (C5) |
| 003 SQLite blackboard | Implemented | `app/core/memory/memory_service.py` | `tests/test_memory.py` | missing 3 artifacts (C5) |
| 004 RAG hardening | Draft (6/21) | `app/core/rag/*` + `manifest.py` | `tests/test_rag/` | manifest done this session |
| 005 Tool registry | Implemented | `app/core/registry/*` | `tests/test_registry/` | brain_v2 -> consolidate (C4) |
| 006 Tactical modules | Implemented | `app/modules/*` | `tests/test_modules/` | - |
| 007 Reflective verification | Implemented | `app/tools/reflective_verification.py` | `tests/test_tools/` | - |
| 008 Self-healing | Implemented | `app/tools/self_heal.py` | `tests/test_tools/` | - |
| 009 GUI (Tkinter) | Implemented (UI superseded by 011) | `app/GUI/desktop_gui.py` | `tests/test_gui/` | fallback only |
| 010 LangGraph agent | Draft (Canonical agent) | `app/core/agent/graph.py`, `nodes/` | - | needs runtime |
| 011 GUI dashboard | Draft | `app/GUI/argus_studio.py` (-> dashboard.py) | - | naming drift (C3) |
| 012 Reconciliation | Canonical | (governance) | validation scripts | complete artifact set |
| 013 LangGraph workflow | Partially superseded | `app/core/workflow/*` | `tests/test_langgraph_workflow.py` | superseded by 010 (C4) |

**Traceability gaps**: 010/011 are specified but not yet implemented against the reconciled core
(blocked on runtime); every other feature maps spec -> code -> tests.

---

## 8. Cleanup Manifest (executable; blocked on delete/runtime here)

Run these in a normal dev checkout (Python 3.12 + deps). Each is safe with the stated precondition.

| ID | Action | Precondition | Priority |
|----|--------|--------------|----------|
| C1 | `rm -rf "Argus-Digilians-fix-copy-setup-to-scripts/"` (nested 1.6 GB self-copy) | confirm not a submodule (it is untracked) | P0 |
| C2 | Delete `app/core/rag/{processor,vectorstore,engine}.py` | grep confirms zero importers (already true) | P0 |
| C3 | Rename `app/GUI/argus_studio.py` -> `dashboard.py`; reduce `app.py`/`argus_gui.py`/`gui_app.py`/`gui_main.py`/`gui_root.py`/`studio.py` to shims, then remove | Streamlit smoke test of dashboard passes | P1 |
| C4 | Merge `brain_v2`->`brain`, `agent_factory_v2`->`agent_factory`; migrate `app/core/workflow/*` into `app/core/agent/`; repoint 3 test files; delete shadows | `pytest` green after repoint | P0 |
| C5 | Author `research.md`/`data-model.md`/`quickstart.md` for `002` and `003-sqlite` | derive from existing spec/plan (no new decisions) | P2 |
| C6 | Move root `*_FIX.*` / `*_REPORT.*` notes to `docs/history/`; delete `Plan md/`; move `check_integration.py`/`test_parsing_fix.py` into `tests/` | none | P2 |
| C7 | Delete `.pytest_cache/` (now gitignored) | none | P3 |

---

## 9. Scores (0-10)

| Dimension | Score | Basis |
|-----------|-------|-------|
| Repository Health | 6.0 | Strong specs/CI; dragged down by 1.6 GB nested copy + root sprawl |
| Spec-Kit Compliance | 8.5 | Canonical 012 authority, traceability, numbering fixed; 6 artifacts missing (C5) |
| Documentation Consistency | 7.0 | Architecture doc canonical; root fix-notes duplicate spec content (C6) |
| Architecture Consistency | 7.0 | Canonical decisions ratified; code still carries two brains/agents (C4) |
| Folder Organization | 5.5 | Nested self-copy, stray `Plan md/`, loose root Python/docs |
| **Overall** | **7.0** | Good engineering core; concentrated, well-understood technical debt |

### Code duplication analysis
- Nested self-copy (1.6 GB, entire tree) - P0.
- 8 GUI entrypoints for 1-2 real UIs - P1.
- 2 brains, 2 factories, 2 agent designs - P0 (behavioral, C4).
- 3 dead RAG forwarders - P0 (C2).

### Documentation duplication analysis
- Architecture: 1 canonical + 1 archived (OK) + ~6 overlapping root guides/notes (C6).
- Fix-notes (9 `*.txt` + several `*_FIX.md`) duplicate content owned by specs 002/013 - consolidate.

### Technical debt summary
Concentrated and well-characterized: one giant duplicate directory, one GUI fan-out, one
brain/agent consolidation, one doc-sprawl cleanup. None are architectural unknowns - all have a
defined canonical target in `012`.

### Remaining refactoring opportunities
C1-C7 above. C1/C2 are pure deletions; C4 is the one behavioral refactor and gates 010/011.

---

## 10. Production Readiness Assessment

**Not yet production-ready**, but close in the parts that matter. The specification layer,
governance (`012`), CI/CD, validation tooling, and the embedding-manifest component are
production-grade. Blocking the release:
1. Remove the nested self-copy (C1) and dead duplicates (C2) - trivial in a real checkout.
2. Land the brain/agent consolidation (C4) so `010`/`011` build on one core - the single most
   important remaining engineering task; needs the test suite.
3. Implement `010` (agent) and `011` (dashboard) against the reconciled core.

**Recommended next step**: in a Python 3.12 checkout with dependencies, execute C1, C2, then C4
(with `pytest` after the test repoint). That clears all P0 debt and unblocks the remaining feature
implementation.
