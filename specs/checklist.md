# Implementation Checklist: Argus Security Framework (Phases 005-014)

**Purpose**: Verify all implementation phases meet spec requirements
**Created**: 2026-06-29
**Updated**: 2026-07-07 — extended to cover Phases 010-014 (previously untracked here; each
phase's own `specs/<phase>/tasks.md` remains the source of truth for individual task items).

---

## Phase 005 — Tool Registry

- [x] CHK001 BaseToolService ABC created in `app/core/registry/base_tool.py`
- [x] CHK002 ToolRegistry class with register/unregister/get_tool/list_tools in `app/core/registry/tool_registry.py`
- [x] CHK003 WSLBridgeTools refactored to use ToolRegistry internally (`app/tools/tool_registry.py`)
- [x] CHK004 14 tools registered via `_register_defaults()` (recon, subdomains, reachability, nikto, ffuf, payloads, secrets, web_search, archive_search, crawler, evasion, self_heal, intelligence, knowledge_graph)
- [x] CHK005 SelfHealingService adapted to implement BaseToolService (`app/tools/self_heal.py`)
- [x] CHK006 ArgusBrainV2 created with dispatch/get_available_tools in `app/core/agent/brain_v2.py`
- [x] CHK007 agent_factory_v2.py with create_default_registry/create_brain/register_all_tools
- [x] CHK008 All 42 legacy WSLBridgeTools methods remain backward-compatible
- [x] CHK009 23 unit tests passing in `tests/test_registry/`

## Phase 006 — Tactical Modules

- [x] CHK010 Import paths fixed in argus_reasoning.py (`core.agent` → `app.core.brain`, `core.tools` → `app.tools.tool_registry`)
- [x] CHK011 Import paths fixed in argus_deep_exploit.py
- [x] CHK012 Import paths fixed in run_recon.py
- [x] CHK013 Import paths fixed in run_full_recon.py
- [x] CHK014 Import paths fixed in map_target.py
- [x] CHK015 Import paths fixed in crawler.py
- [x] CHK016 BaseTacticalModule ABC in `app/modules/base.py`
- [x] CHK017 `__init__.py` refactored with register/run_all/run_module/list_modules
- [x] CHK018 12 import tests passing in `tests/test_modules/`

## Phase 007 — Reflective Verification

- [x] CHK019 In-memory command history tracking in `ReflectiveVerificationService`
- [x] CHK020 Infinite-loop detection: 3+ identical consecutive commands blocked
- [x] CHK021 History limited to last 10 entries (MAX_HISTORY = 10)
- [x] CHK022 Delegation methods in WSLBridgeTools: verify_command, verify_output, assess_difficulty
- [x] CHK023 3 new tools registered: verify_command, verify_output, assess_difficulty
- [x] CHK024 20 unit tests passing in `tests/test_tools/test_reflective_verification.py`

## Phase 008 — Self-Healing

- [x] CHK025 health_check() method with WSL/Ollama/Python checks
- [x] CHK026 `_check_wsl()` via subprocess (wsl --status)
- [x] CHK027 `_check_ollama()` via HTTP GET localhost:11434/api/tags
- [x] CHK028 `_check_python()` verifying sys.version and venv
- [x] CHK029 restart_service(name) for ollama and wsl
- [x] CHK030 `_restart_ollama()` (taskkill + ollama serve)
- [x] CHK031 `_restart_wsl()` (wsl --terminate + verify)
- [x] CHK032 system_self_heal unchanged (backward-compatible)
- [x] CHK033 10 unit tests passing in `tests/test_tools/test_self_heal.py`

## Phase 009 — GUI

- [x] CHK034 Imports fixed in argus_gui.py (`core.*` → `app.*`)
- [x] CHK035 desktop_gui.py created (Tkinter desktop with target input, run button, output area)
- [x] CHK036 Graceful Tkinter fallback: clear error if Tkinter not installed
- [x] CHK037 studio.py created as alias re-exporting app.py
- [x] CHK038 3 import validation tests passing in `tests/test_gui/`

## Cross-Cutting

- [x] CHK039 All 88 tests pass (pytest tests/ -v)
- [x] CHK040 All Phase 005-009 tasks committed with descriptive messages
- [x] CHK041 Commit strategy followed (commit per completed phase)
- [x] CHK042 Architecture v2 alignment maintained across all phases

---

## Phase 010 — LangGraph Agent

- [x] CHK043 `build_tactical_graph()` implements recon → scanner → exploit → reflective →
  self_heal/post_exploit as a LangGraph `StateGraph` (`app/core/agent/graph.py`)
- [x] CHK044 Conditional `reflective → {exploit, END}` edge added so an exhausted retry
  budget ends the run instead of guaranteeing one more failed exploit attempt
  (`app/core/agent/graph.py::_route_after_reflective`)
- [x] CHK045 Recon degrades explicitly (never silently) when nmap can't confirm a port:
  `-Pn` retry tagged `ports_scan_degraded`, whatweb-confirmed scheme-port inference tagged
  `ports_inferred` (`app/tools/recon.py`, `app/core/agent/nodes/recon.py`)
- [x] CHK046 Scanner falls back to the target's own URL scheme when `open_ports` is empty
  and persists it back into state so exploit doesn't redundantly fail
  (`app/core/agent/nodes/scanner.py`)
- [x] CHK047 30/33 tasks checked in `specs/010-langgraph-agent/tasks.md`; remaining 3
  (T027/T029/T031-T033-range) are explicitly tracked as out-of-scope, not silent gaps
- [x] CHK048 163/163 pytest passing per CHANGELOG.md validation entry (2026-07-07),
  excluding one pre-existing unrelated network-dependent test

## Phase 011 — GUI Enhancement

- [x] CHK049 Non-functional Blackboard status, Knowledge Graph, and dashboard buttons wired
  to real backend data (commit `179e979`)
- [x] CHK050 Blocking sleep-loop polling replaced with non-blocking `st.fragment` (commit `1186adb`)
- [x] CHK051 Agent state-file write race between parent/child process removed (commit `194dbc5`)
- [ ] **CHK052 (OPEN — tracking gap)** `specs/011-gui-enhancement/tasks.md` still shows 0/31
  tasks checked (`[ ]` on every line) despite the corresponding code (`app/GUI/dashboard.py`,
  `agent_controller.py`, `blackboard.py`, etc.) existing and the fixes above being merged and
  live-validated. The work is done; the tracking file was never updated to reflect it. **Action
  owner must reconcile `specs/011-gui-enhancement/tasks.md` against actual code before this
  phase can be marked compliant** — not fixed in this pass, since marking 31 individual items
  done requires per-item code verification, not a blanket check.

## Phase 012 — Spec Reconciliation

- [x] CHK053 32/33 tasks checked in `specs/012-spec-reconciliation/tasks.md`

## Phase 013 — LangGraph Workflow

- [x] CHK054 34/34 tasks checked in `specs/013-langgraph-workflow/tasks.md`

## Phase 014 — Containerized Lab

- [ ] CHK055 5/13 tasks checked in `specs/014-containerized-lab/tasks.md` — in progress
- [x] CHK056 `deploy/docker-lab/{Dockerfile,docker-compose.yml}` present, version-pinned
  (`ollama/ollama:0.3.14`, `juice-shop:v17.1.1`, gobuster 3.6.0, ffuf 2.1.0, subfinder 2.6.6 — FR-006)
- [x] CHK057 Lab is additive/optional and does not alter the WSL production path (FR-007)

---

## Summary

| Metric | Value |
|--------|-------|
| Phases completed | 5 (005-009) fully; 010/012/013/014 substantially; 011 code-complete but tracking-stale |
| Tasks completed | 60+ (005-009) + 30/33 (010) + 0/31-tracked-but-code-complete (011) + 32/33 (012) + 34/34 (013) + 5/13 (014) |
| Tests written | 68 (new, 005-009) |
| Total tests passing | 163/163 per latest CHANGELOG.md validation (2026-07-07) |
| Commits | 16+ (005-009) + ongoing |
| New files created | 20+ (005-009) |
| Files refactored | 10+ (005-009) |
| **Open compliance gaps** | **CHK052** (011 task tracking vs. code mismatch); **CHK055** (014 in progress, not a gap — expected) |
