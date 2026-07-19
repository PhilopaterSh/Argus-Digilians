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
  `REACT_FORMAT_ERROR_FIX.txt`, `RADICAL_FIX_SIMPLE_CHAIN_FALLBACK.txt`, etc.) -
  **update (2026-07-10)**: these 6, plus `IMPLEMENTATION_GUIDE_parsing_error_fix.md` and
  `QUICK_START_FIX.txt` (7 total, all documenting the same 2026-06-25 incident), were
  consolidated into one chronological file,
  `docs/history/2026-06-25_react_parsing_and_simplechain_fallback_incident.md`, and deleted -
  see that file's own header for why (and for the connection to `018`'s later finding that the
  fix these 7 files describe never actually worked).
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

### STATUS: C3 done (2026-07-06)
`argus_studio.py` renamed to `app/GUI/dashboard.py` (`STREAMLIT_DASHBOARD_ENTRYPOINT` in
`app/core/agent/contracts.py`, `config.yaml`'s `gui_entry`, and `app/core/config.py`'s
`PathSettings.gui_entry` default all updated to match - the latter two had been silently
pointing at `gui_app.py`, a single-purpose demo script, not the real dashboard). Launchers
(`scripts/LAUNCH_STUDIO.bat`, `scripts/TEST_ARGUS.bat`) repointed. `app.py`, `argus_gui.py`,
`gui_main.py`, `gui_root.py` now carry the same `DeprecationWarning` + in-page banner pattern
`app.py` already used (their functional bodies were left intact rather than gutted, to avoid
behavior risk); `studio.py` re-exports `dashboard.py` directly instead of chaining through the
deprecated `app.py`. `gui_app.py` also deprecated the same way but NOT wired anywhere anymore -
note its body unconditionally runs a live agent analysis against a hardcoded target on import
(no button gate), so it must never be added to an import-based smoke test. Full physical removal
of the 6 shims deferred to a follow-up pass (needs a broader UI regression check first).
Validated via `tests/test_gui/` (17 passed) and the full suite (144 passed).

### Problems found (original, 2026-07-05)
- **P0 - 8 overlapping entrypoints**: `app.py`, `argus_gui.py`, `argus_studio.py`,
  `desktop_gui.py`, `gui_app.py`, `gui_main.py`, `gui_root.py`, `studio.py`. The canonical
  primary UI per `012` section 2.5 / `011` is a single `app/GUI/dashboard.py`, which does not
  yet exist; `argus_studio.py` appears to be the closest current implementation.
- **P1 - Naming drift**: `011` specifies `dashboard.py`; the code uses `argus_studio.py`.

### Improvements applied
- See STATUS above - C3 is now done.

### Recommendation
Physically remove the 6 deprecation shims once a full UI regression pass confirms nothing
external still launches them directly.

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
  `docs/ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md` (archived - acceptable; moved to
  `docs/history/ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md` 2026-07-10 as part of a repo-wide
  organization pass, per its own self-declared "LEGACY" status), plus root
  `Argus_Master_Documentation.md`, `INSTALLATION_GUIDE.md`, `INSTALL*.md`, and multiple
  `*_FIX.md`/`*_REPORT.md` that overlap installer/parsing content already owned by specs
  `002`/`013`.
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
| 010 LangGraph agent | Implemented, but **superseded as production driver by 017** (2026-07-08) | `app/core/agent/graph.py`, `nodes/` | `tests/test_modules/{test_agent_contracts,test_tactical_graph_termination}.py`, `tests/test_gui/{test_dashboard,test_agent_tab_status}.py` | Code + tests retained (Constitution VII); no longer invoked by `scripts/run_agent.py` |
| 011 GUI dashboard | Draft (entrypoint done, tabs partial) | `app/GUI/dashboard.py` | `tests/test_gui/` | renamed 2026-07-06 (C3 done) |
| 012 Reconciliation | Canonical | (governance) | validation scripts | complete artifact set |
| 013 LangGraph workflow | Superseded as a standalone feature, but its custom graph is **actively reused by 018** as of 2026-07-08 | `app/core/agent/react_workflow.py` (was `app/core/workflow/*`) | `tests/test_langgraph_workflow.py` | migration completed 2026-07-06 (C4/T028); no longer dead code - see 018 |
| 017 Restore ReAct agent | Implemented, internals revised by 018 | `app/core/agent/{brain_tools,react_callback}.py`, `scripts/run_agent.py`, `app/core/agent/brain.py` (pre-existing) | `tests/test_registry/{test_brain_tools,test_react_callback}.py`, `tests/test_modules/test_run_agent.py` | `ArgusBrain` drives production "Start Agent"; 010's graph retained, not deleted |
| 018 Structured agent reliability | Implemented, addendum (2026-07-09) fixed 4 more live bugs + 1 mitigated infra crash | `app/core/agent/brain.py` (rewired + target-extraction fix + infra-crash retry), `app/core/agent/react_workflow.py` (+structured final-answer, +max_iterations bug fix), `app/core/agent/react_callback.py` (+on_graph_event), `app/core/llm_factory.py` (+`build_chat_llm`), `app/core/memory/memory_service.py` (bounded `get_blackboard_summary`), `scripts/LAUNCH_STUDIO.bat` (KV-cache quantization) | `tests/test_registry/test_brain_ask.py`, `tests/test_registry/test_react_callback.py`, `tests/test_langgraph_workflow.py`, `tests/test_memory.py` | Fixes a live 900s-timeout/zero-results production failure, then 4 more real bugs (OllamaLLM/ChatOllama structured-output gap, unbounded Blackboard context, prebuilt/custom graph routing mismatch, target-extraction ordering) found in a live re-run - see `specs/018-structured-agent-reliability/{spec,research,tasks}.md` addenda, `specs/checklist.md` CHK077-082; `app/core/prompts.py` (017's original prompt) is no longer what drives tool selection - `ArgusBrain` now uses `react_workflow.py`'s shorter `react_prompts.py` + structured decoding for reliability; `app/core/prompts.py` remains used by `agent_factory.py`'s classic executor, kept for other callers |
| 019 Shared-memory + Dual-Phase Reflection upgrade | **Implemented 2026-07-10** | `app/core/memory/memory_service.py` (+`summarize_for_planning`), `app/core/agent/react_workflow.py` (+`_build_reflection_note`, `_inter_reflect`, `_check_early_termination`, `EXPLOITATION_TOOLS`), `app/core/agent/react_state.py` (+`reflection_notes`), `app/core/agent/react_prompts.py` (+reflection block), `app/core/agent/brain.py` (+`enable_inter_reflection` wiring, `_emit_graph_step` `"reflecting"` status), `config.yaml`/`app/core/config.py` (+`enable_inter_reflection`) | `tests/test_memory.py` (+5), `tests/test_langgraph_workflow.py` (+13), plus one manual integration smoke test (7/7 assertions) | Two deviations from the original plan, both found by reading the real code before implementing rather than assuming: (1) `get_blackboard_summary()` left untouched (its exact shape is asserted by existing tests/consumed as-is by other callers) - the new per-source-bounded capability lives in the new, additive `summarize_for_planning()` instead; (2) reflection observability implemented via `"Reflection:"`-prefixed messages flowing through `brain.py`'s existing per-message stream loop, not new callback plumbing threaded into `react_workflow.py`'s node functions (which don't receive callbacks at all). T013 (live wall-clock cost) measured against the real production model: `enable_inter_reflection=true`'s 3x-vote adds ~0.82s vs. a normal ~10.96s action-generation call (~8%, not ~300%) - the vote's one-word-constrained output makes it cheap regardless of being 3 calls; confirmed safe as the default. Full regression: 239/240 repo-wide, the 1 failure (`test_smart_web_search.py`) confirmed pre-existing/unrelated via `git stash`. See `specs/019-shared-memory-reflection-upgrade/tasks.md`, `specs/checklist.md` CHK091-100 |
| 020 Multi-agent role separation | **Implemented as an experimental, feature-flagged-off path (2026-07-11)** - NFR-001 measured 2.00x LLM call-count overhead vs. the single-loop baseline (borderline, at the spec's own 2x rollback threshold); `enable_multi_agent_roles` stays `false`, not promoted to default | `app/core/agent/react_workflow.py` (+`_build_multi_role_workflow`, `_PlannerDecision`/`_try_planner_decision`, `_parse_react_output` extracted to module level), `app/core/agent/react_prompts.py` (+4 role prompts), `app/core/agent/brain_tools.py` (+`ROLE_TOOL_PARTITIONS`, `role=` param, `partition_tools_by_role`), `app/core/agent/react_state.py` (+`current_role`/`role_history`), `app/core/agent/brain.py` (+conditional routing), `config.yaml`/`app/core/config.py` (+`enable_multi_agent_roles`) | `tests/test_registry/test_react_prompts.py` (+5), `tests/test_registry/test_brain_tools.py` (+9), `tests/test_langgraph_workflow.py` (+8), `tests/manual/specs020_wallclock_comparison.py` (NFR-001 measurement harness) | User first proposed a heavier multi-model variant (Dolphin/DeepSeek-Coder/abliterated Llama-3-8B per role) - researched and rejected in favor of this spec's original single-model FR-001 scope (VRAM math doesn't hold on this machine's 16GB, abliteration regresses TruthfulQA specifically, Persona-Pruner research validates the single-dense-model direction); see `specs/020-multi-agent-role-separation/research.md`'s 2026-07-11 addendum and `tasks.md` T000-T010 for the full record |
| 021 Specialized exploitation toolkit | **Proposed** (spec kit only, 2026-07-10) | not started | not started | JWT/IDOR/file-upload/XSS-fuzzer/code-injection(SSTI/XXE) tools, per-tool independently shippable - see `specs/021-specialized-exploitation-toolkit/` |
| 022 Browser automation via Playwright | **Proposed** (spec kit only, 2026-07-10) | not started | not started | Closes the JS-rendering blind spot in `crawler.py`'s curl-only pipeline; new Kali-side runtime dependency - see `specs/022-browser-automation-playwright/` |
| 023 CVE intelligence & PoC retrieval | **Proposed** (spec kit only, 2026-07-10) | not started | not started | Distinct from existing `payloads.py`/`web_search.py` (neither does version-to-CVE correlation) - see `specs/023-cve-poc-intelligence/` |
| 024 LoRA fine-tuning pipeline | **Proposed** (spec kit only, 2026-07-10) | not started | not started | Offline training pipeline, isolated from `app/`'s runtime deps; base-model choice left as an open decision - see `specs/024-lora-fine-tuning-pipeline/` |
| 025 Subtask-level benchmark suite | **Proposed** (spec kit only, 2026-07-10) | not started | not started | Also fixes an existing gap in `tests/ai_benchmark.py` (hand-picked 2-tool subset instead of production's real `build_argus_tools()`) as part of its migration - see `specs/025-subtask-benchmark-suite/` |
| 026 Ethical safeguards | **Proposed** (spec kit only, 2026-07-10) | not started | not started | Scoped down from the paper's full RBAC/audit/watermarking proposal to match Argus's single-operator local-tool deployment shape - see `specs/026-ethical-safeguards-raii/spec.md`'s "Why this is scoped down" |

**Traceability gaps**: 011 (GUI dashboard tabs) still has real unimplemented scope; 010 has
two specific missing tests (T027: tactical graph termination, T029: failed-vs-running UI
distinction) rather than being unimplemented outright. Every other implemented feature maps
spec -> code -> tests. `021`-`026` remain **intentionally** spec-kit-only (a backlog produced
from a 2026-07-10 gap analysis against `docs/history/2603.27127v1.pdf`, at the user's request) -
not implementation gaps, since no code was ever claimed for them; `019` and `020` (same backlog)
have since been implemented (`020` as an experimental, feature-flagged-off path - see its row
above), see their rows above. See `specs/checklist.md`'s "Backlog - Proposed Future Phases"
section for sequencing recommendations on the rest.

---

## 8. Cleanup Manifest (executable; blocked on delete/runtime here)

Run these in a normal dev checkout (Python 3.12 + deps). Each is safe with the stated precondition.

| ID | Action | Precondition | Priority | Status |
|----|--------|--------------|----------|--------|
| C1 | `rm -rf "Argus-Digilians-fix-copy-setup-to-scripts/"` (nested 1.6 GB self-copy) | confirm not a submodule (it is untracked) | P0 | Done (2026-07-06) - verified via byte-level diff of its own unresolved-merge working tree against commit `8495f4d`: `tool_registry.py` identical, `brain.py`/`config.yaml` differed only by already-superseded fixes (ASCII cleanup, port correction). Zero unique content confirmed before deletion; owner confirmed explicitly. |
| C2 | Delete `app/core/rag/{processor,vectorstore,engine}.py` | grep confirms zero importers (already true) | P0 | Done |
| C3 | Rename `app/GUI/argus_studio.py` -> `dashboard.py`; reduce `app.py`/`argus_gui.py`/`gui_app.py`/`gui_main.py`/`gui_root.py`/`studio.py` to shims, then remove | Streamlit smoke test of dashboard passes | P1 | Rename+shims done (2026-07-06). **Precondition met** (2026-07-06): `tests/test_gui/test_dashboard_apptest.py` uses Streamlit's `AppTest` harness to actually run `dashboard.py` and each of its 6 tabs in a simulated session (not just import) - zero exceptions. **Done (2026-07-10)**: `app.py`/`argus_gui.py`/`gui_main.py` were found to NOT be simple shims despite this table's own earlier wording - each was a full, independently-running 90-180-line Streamlit app with its own hardcoded, drifted tool list (confirmed live: none matched the canonical 17-tool `brain_tools.py` list). All 3 converted to true one-line `from app.GUI.dashboard import *` re-exports (matching `studio.py`'s existing pattern); `tests/test_gui/` (35 tests) confirmed green after. `gui_app.py`/`gui_root.py` were already deleted 2026-07-06 (see below). |
| C4 | Merge `brain_v2`->`brain`, `agent_factory_v2`->`agent_factory`; migrate `app/core/workflow/*` into `app/core/agent/`; repoint 3 test files; delete shadows | `pytest` green after repoint | P0 | Done |
| C5 | Author `research.md`/`data-model.md`/`quickstart.md` for `002` and `003-sqlite` | derive from existing spec/plan (no new decisions) | P2 | Done - all 6 files already present with substantial content (91-139 lines each), verified 2026-07-06 |
| C6 | Move root `*_FIX.*` / `*_REPORT.*` notes to `docs/history/`; delete `Plan md/`; move `check_integration.py`/`test_parsing_fix.py` into `tests/` | none | P2 | Done - `test_parsing_fix.py` routed to `docs/history/verify_parsing_fix.py` instead of `tests/` (2 of its 4 assertions fail against current design; `tests/` would have made it live for the first time via pytest's `test_*.py` discovery). Follow-up (2026-07-09): `IMPLEMENTATION_GUIDE.md` was missed by the original C6 pass because its name doesn't match the `*_FIX.*`/`*_REPORT.*` glob, despite its content being exactly that (a one-off writeup of the same "Invalid Format: Missing 'Action:'" bug `PARSING_ERROR_FIX.md` already covers) - moved to `docs/history/IMPLEMENTATION_GUIDE_parsing_error_fix.md`. **Further follow-up (2026-07-10)**: `check_integration.py` and `verify_parsing_fix.py` were still sitting in `docs/history/`/`tests/` root respectively, not properly separated from the real pytest suite - both moved into a new `tests/manual/` (alongside 4 other ad hoc scripts found the same way, see `tests/manual/README.md`), with their now-one-level-deeper relative import paths fixed and verified live. `IMPLEMENTATION_GUIDE_parsing_error_fix.md`/`PARSING_ERROR_FIX.md`/`JSON_PARSING_FIX.md`/`REACT_FORMAT_ERROR_FIX.txt`/`RADICAL_FIX_SIMPLE_CHAIN_FALLBACK.txt`/`QUICK_START_FIX.txt`/`TESTING_JSON_FIX.md` (7 files, all documenting the same 2026-06-25 incident) consolidated into one file and deleted - see `docs/history/2026-06-25_react_parsing_and_simplechain_fallback_incident.md`. |
| C7 | Delete `.pytest_cache/` (now gitignored) | none | P3 | Done |

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

---

## 11. Follow-up: GUI crash fix + repo-wide import-time side-effect sweep (2026-07-06)

All of section 10's blockers (C1-C7) are now done - see the Cleanup Manifest table (section 8)
status column. This section documents a follow-up pass done in a real dev checkout with the full
test suite available.

**Crash-class defect found and fixed**: `app/GUI/gui_app.py` and `app/GUI/gui_root.py` both
executed `brain.ask()` unconditionally at import time (no button gate), crashing with
`'NoneType' object has no attribute 'update'` in bare-mode Streamlit without live Ollama/WSL.
Verified 98% identical to each other and fully superseded by `app/GUI/dashboard.py`'s
`AgentController`-based Agent tab. **Both deleted.**

**Repo-wide sweep** (`app/core/`, `app/tools/`, `app/modules/`, `scripts/*.py`; GUI package
covered separately above) for the same defect class - module-level code executing at import
instead of being deferred into a function or gated by `if __name__ == "__main__":`. Found and
fixed two real, low-severity cases (neither could crash without live services - both were pure
local file/DB I/O, but violated the "deterministic imports" principle):
- `app/core/agent/blackboard.py` created the SQLite schema unconditionally on import (`init_schema()`
  called at column 0). Fixed: deferred to lazy init on first `get_connection()` call via a
  `_schema_ready` guard.
- `app/core/agent/graph.py` read `config.yaml` via `ArgusConfig.load()` at import to set
  `MAX_RETRIES`. Fixed: moved into `_get_max_retries()`, called from `should_continue()`.

Reviewed and left unchanged (standard, low-risk bootstrap patterns, not accidental side effects):
`app/tools/wsl_bridge.py`'s `load_dotenv()` at import; `scripts/run_argus_cli.py`'s
`load_dotenv()`/`ArgusConfig.load()` before its `__main__` guard.

Validated: full suite (144 passed), `ruff` clean, `scripts/validate_ascii.py` /
`scripts/validate_specs.py` both PASS.

---

## 12. Full install-to-runtime audit pass (2026-07-06)

A deliberately end-to-end pass, from installer syntax through actual GUI runtime behavior,
conservatively scoped to what this sandboxed environment can genuinely verify.

**Install/setup**: `scripts/ARGUS_INSTALLER.ps1` and all first-party `.ps1` files re-verified
via `[System.Management.Automation.Language.Parser]::ParseFile` (zero parse errors) - this is
static syntax validation only; the installer's actual WSL/Kali/Ollama provisioning steps cannot
be executed in this environment (no admin elevation, no WSL). This limitation is unchanged from
every prior pass this session and is called out explicitly rather than assumed away.

**Project structure/imports**: re-confirmed via `python -m compileall -q app scripts tests
workspace` (zero errors) and the full pytest collection (163 tests collected without error).

**Hidden-issue sweep** (import-time execution, unguarded service calls, misleading UI state):
no new instances found beyond what earlier passes this session already fixed (`app/GUI/gui_app.py`/
`gui_root.py` deleted, `app/core/agent/{blackboard,graph}.py` deferred). This pass specifically
looked for anything missed and found nothing new.

**New verification depth added this pass**: prior passes only checked that GUI modules *import*
without exception (via `importlib.import_module`). This pass used Streamlit's `AppTest` harness
(`streamlit.testing.v1`) to actually *run* `dashboard.py` end-to-end, including navigating to
all 6 tabs (Dashboard, Targets, Agent, Knowledge Graph, Reports, Settings) in a simulated
session - a materially stronger guarantee than an import check, and the first time this
repository's GUI has had genuine runtime verification without a human manually clicking through
it. Zero exceptions. Persisted as `tests/test_gui/test_dashboard_apptest.py` (7 tests) so this
guarantee doesn't regress silently.

**CLI**: `python scripts/run_argus_cli.py --help` runs and exits 0 with correct usage text.

Validated: full suite (163 passed), `ruff` clean, both validators PASS, PowerShell syntax gate
clean, CLI `--help` invocation succeeds.

### Correction (2026-07-07): live WSL/Ollama/SSH were actually available all along

Everything above (and every prior pass in this document) stated live Ollama/WSL/SSH were
unavailable "in this sandboxed environment." That was wrong - none of those passes actually
attempted a live invocation; the assumption was never tested. Direct verification in a
follow-up session found:
- `wsl.exe` is reachable and `kali-linux` boots and runs real commands.
- Ollama is running with `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` already pulled (15 GB);
  a real `/api/generate` call returned a real response. `ArgusBrain.simple_ask()` (the actual
  project code, not a probe script) confirmed the same end-to-end.
- SSH inside Kali was installed but dormant (`inactive (dead)`, disabled at boot) - starting it
  (`mkdir -p /run/sshd && /usr/sbin/sshd`, exactly what `WSLBridge.ensure_ssh_service()` already
  does) brought port 22 up immediately; `paramiko` connected with the project's default
  `kali`/`kali` credentials and executed a real remote command.
- `scripts/LAUNCH_STUDIO.bat` was run for real (non-interactively): Ollama check passed, SSH
  self-heal fired and succeeded, and the Streamlit dashboard came up and served real HTTP 200
  content on the configured port (12199). **No script or code change was needed to make this
  work** - the launcher's self-healing logic was already correct.

One genuine, minor, previously-undiscovered bug was found and fixed in the process:
`app/tools/self_heal.py`'s `_check_wsl()` decoded `wsl.exe`'s UTF-16LE stdout/stderr with
`text=True` (platform-default encoding), producing an unreadable, null-byte-interleaved
diagnostic message in the failure path only - the actual pass/fail result was always
`returncode`-based and unaffected. Fixed to decode explicitly as `utf-16-le`.

The only items that remain genuinely unverified are a full autonomous recon->exploit->report
run against a real external target (a live pentest, out of scope to run casually against any
target) and the fresh-machine installer provisioning steps (WSL feature enablement, Kali
first-install) - both are legitimately different from "the components don't exist," which was
the incorrect framing used throughout this document until now.
