# Tasks: GUI Enhancement - Professional Security Dashboard

**Input**: Design documents from `/specs/011-gui-enhancement/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

**Reconciliation note (2026-07-09, closes CHK052)**: this file showed 0/31 unchecked despite the
work being done and merged (`179e979`, `1186adb`, `194dbc5`) - the tracking file was simply never
updated. Every item below was individually re-verified against the actual current code (function/
class names grepped directly, not assumed) before being checked off. One systematic naming
difference applies throughout: the spec calls the per-page modules `app/GUI/pages/*.py`; the
actual implementation uses `app/GUI/tabs/*.py` instead (same intent, renamed during
implementation - `pages/dashboard.py` -> `tabs/overview.py`, `pages/agent.py` -> `tabs/agent.py`,
etc.). Noted once here rather than repeated on every affected line.

## Phase 1: Setup & Foundation

**Purpose**: Project initialization, path fixes, and shared utilities

- [x] T001 [P] `scripts/LAUNCH_STUDIO.bat` resolves `app/GUI/dashboard.py`, sets `PYTHONPATH`
  (line 95), and checks for the venv (lines 88-89) - verified directly in the file.
- [x] T002 [P] Package `__init__.py` files exist for `app/GUI/components/`, `app/GUI/utils/`, and
  `app/GUI/tabs/` (the actual page-module directory - see naming note above; there is no
  `app/GUI/pages/` since that convention was never used).
- [x] T003 [P] `app/GUI/utils/blackboard.py` has all five required functions
  (`load_targets`/`save_target`/`load_findings`/`load_entities`/`load_relations`), plus
  `get_blackboard_counts`/`build_graph_data` added later (T004/T021).
- [x] T004 [P] `app/GUI/components/status_bar.py::render_status_bar()` shows Ollama status
  (`check_ollama_status`), SSH bridge status (`check_ssh_status`), and Blackboard target/finding
  counts (via `get_blackboard_counts()` - see the Post-Implementation Bug Fixes section below for
  the fix that made this real instead of always "N/A").
- [x] T005 `gui_sessions` and `gui_jobs` tables exist in `app/core/memory/memory_service.py`
  (and, redundantly, in `app/GUI/utils/blackboard.py::init_gui_tables()` - a small duplication
  worth a future look, not part of this reconciliation pass).

---

## Phase 2: User Story 1 - Unified Professional Dashboard (Priority: P1) 🎯 MVP

**Goal**: Single multi-page Streamlit dashboard that replaces all existing GUIs

- [x] T006 `app/GUI/dashboard.py` is the main entry point: session-state init for
  targets/jobs/settings (dark theme default), `render_status_bar()` at the top, and sidebar
  navigation (`nav_radio`, proven working under `AppTest` per the bug-fixes section below).
- [x] T007 [P] `app/GUI/tabs/overview.py::render_dashboard()` (the `pages/dashboard.py`
  equivalent - see naming note) has recent-activity loading (`_load_recent_runs`) and the
  system/health overview.
- [x] T008 [P] `app/GUI/tabs/settings.py::render_settings()` has model name input, Ollama
  endpoint input, SSH credentials, theme selector, session save/load controls, and a log viewer.
- [x] T009 [P] `app/GUI/static/style.css` exists (dark terminal theme).
- [x] T010 `app/GUI/__init__.py` does path setup; re-checked whether any code actually imports
  `from app.GUI import <dashboard class>` expecting re-exports - nothing does, so the specific
  backward-compatibility concern this task anticipated never materialized. Not a gap in practice.
- [x] T011 Import validation is a live pytest parametrized test,
  `tests/test_gui/test_imports.py::test_gui_module_imports[app.GUI.dashboard]` - stronger than a
  one-off manual `python -c` check, and it passes.

---

## Phase 3: User Story 2 - LangGraph Agent Integration (Priority: P1)

**Goal**: Live agent control interface with real-time node transition visualization

- [x] T012 [P] `app/GUI/utils/agent_controller.py::AgentController` has `start()`, `stop()`,
  `get_status()`, and `get_feed()` exactly as specified.
- [x] T013 `app/GUI/tabs/agent.py::render_agent()` has the target selector, Start/Stop buttons,
  a live feed panel (`_render_events`), current-state display, and a Final Results panel.
- [x] T014 `AgentController` writes JSON state to `logs/agent_runs/` (see its `state_dir`); the
  Agent tab polls and renders it via `get_status()`/`get_feed()`.
- [x] T015 Test: satisfied by the Post-Implementation Bug Fixes section's documented live
  end-to-end runs against `scanme.nmap.org` ("the third completed the full recon -> scanner ->
  exploit -> reflective retry loop -> completion... with real findings in final_state") - a
  stronger verification than a single manual GUI click-through would have been.

---

## Phase 4: User Story 3 - Target & Session Management (Priority: P2)

**Goal**: Multi-target management with persistent sessions

- [x] T016 [P] `app/GUI/tabs/targets.py::render_targets()` has the Add Target form and a
  search/filter bar over the target list.
- [x] T017 [P] `app/GUI/components/session_manager.py` has all four required functions
  (`save_session`/`load_session`/`list_sessions`/`delete_session`); its DB-connection helper was
  deduplicated against `app/GUI/utils/blackboard.py`'s identical copy in this same session
  (CHK061) into `app/GUI/utils/db_connection.py`.
- [x] T018 Session save/load is wired into `app/GUI/tabs/settings.py` (imports and calls
  `save_session`/`load_session` directly).
- [x] T019 Test: covered by `tests/test_gui/test_session.py::test_multiple_sessions` (adds 3
  sessions, verifies all list and delete correctly) and `test_session_save_and_load_roundtrip`.

---

## Phase 5: User Story 4 - Knowledge Graph Visualization (Priority: P2)

**Goal**: Interactive entity-relationship graph from Blackboard data

- [x] T020 `app/GUI/tabs/knowledge_graph.py::render_knowledge_graph()` (the `pages/
  knowledge_graph.py` equivalent) renders a Pyvis graph with a type->color map, click-through
  entity details, and a search/filter box.
- [x] T021 `build_graph_data()` in `app/GUI/utils/blackboard.py` builds a real NetworkX graph
  from `ArgusMemory.get_findings_graph_rows()` - see the Post-Implementation Bug Fixes section
  below for the fix that replaced an always-empty stub with this.
- [x] T022 Test: covered by the same live end-to-end validation cited for T015 (recon populated
  real findings, and this session's own live testing confirmed the Knowledge Graph tab renders
  them, not an empty graph).

---

## Phase 6: User Story 5 - Advanced Reporting (Priority: P3)

**Goal**: Professional report export in multiple formats

- [x] T023 [P] `app/GUI/components/export.py` has all four required functions
  (`generate_html_report`/`generate_markdown_report`/`generate_json_report`/`get_available_templates`).
- [x] T024 `app/GUI/tabs/reports.py::render_reports()` has a format selector (HTML/Markdown/JSON),
  a Generate button, and a Download button.
- [x] T025 `app/GUI/templates/reports/default.html` exists (Jinja2 template, professional
  styling).
- [x] T026 Test: covered by `tests/test_gui/test_dashboard.py::test_export_html_report` (and its
  markdown/json siblings), which verify real generated report content.

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: Tests, documentation, backward compatibility

- [x] T027 [P] `tests/test_gui/test_dashboard.py` exists with 9 test functions covering imports
  (dashboard/tabs/components/utils) and export/agent_controller/session_manager smoke tests.
- [x] T028 [P] `tests/test_gui/test_session.py` exists with session save/load round-trip tests.
- [x] T029 [P] Both `app/GUI/app.py` and `app/GUI/argus_gui.py` emit a `DeprecationWarning`
  pointing at `dashboard.py`.
- [x] T030 [P] Full suite re-verified in this same reconciliation pass: 186 passed, 1
  pre-existing unrelated failure (`test_smart_web_search.py::test_attempt_limit`).
- [x] T031 Commit history confirms this: `179e979` ("wire Blackboard status, Knowledge Graph,
  and dashboard buttons to real data"), `1186adb`, `194dbc5`, among others.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Dashboard (Phase 2)**: Depends on Phase 1
- **Agent (Phase 3)**: Depends on Phase 2 (dashboard framework), requires 010-langgraph-agent code
- **Targets/Sessions (Phase 4)**: Depends on Phase 2, can run in parallel with Phase 3
- **Knowledge Graph (Phase 5)**: Depends on Phase 4 (targets in session), requires Blackboard data
- **Reporting (Phase 6)**: Depends on Phase 3 (findings from agent)
- **Polish (Phase 7)**: Depends on all phases

### Parallel Opportunities

- T001-T005 can run in parallel (Phase 1)
- T007-T009 can run in parallel (Phase 2 pages)
- Phase 3 and Phase 4 can run in parallel
- T020 and T023 can run in parallel (Phase 5 and 6 components)
- T027-T028 can run in parallel (Phase 7 tests)

---

## Post-Implementation Bug Fixes (2026-07-07)

Diagnosed against a real, fully-online environment (Ollama/SSH/WSL all confirmed
live) - the reported "GUI slow, buttons do nothing, no results" symptoms were
execution-flow/UI-logic bugs, not infrastructure. Six confirmed root causes,
each verified by reading the actual code (not assumed) and, where applicable,
by live end-to-end reproduction against `scanme.nmap.org`.

### 1. Dashboard "Quick Action" buttons were fully non-functional
- **Broken**: `app/GUI/tabs/overview.py`'s 4 buttons (New Target / Start Agent /
  Generate Report / Settings) set `st.session_state.targets_tab_open` (etc.)
  and called `st.rerun()`. Nothing anywhere read those flags.
- **Why**: `app/GUI/dashboard.py`'s page routing is driven entirely by
  `st.sidebar.radio(key='nav_radio')`. Setting an unrelated flag has no effect
  on which page renders - clicking any of the 4 buttons produced a rerun with
  zero visible change.
- **Fixed**: buttons now set `st.session_state.nav_radio` directly (the exact
  key the sidebar widget reads its value from) before rerunning, so each
  button performs real navigation to the intended tab.
- **Evidence**: `tests/test_gui/test_dashboard_apptest.py` already drives
  navigation via `at.radio(key="nav_radio").set_value(page)` - the same
  mechanism, proven working under `AppTest` for all 6 pages with zero
  exceptions after the fix.

### 2. Blackboard status showed "N/A" unconditionally
- **Broken**: `app/GUI/components/status_bar.py` called
  `get_blackboard_summary().get("target_count", 0)`.
- **Why**: `ArgusMemory.get_blackboard_summary()`
  (`app/core/memory/memory_service.py`) returns a **JSON string** of nested
  per-domain detail, not a dict. `.get()` on a string always raises
  `AttributeError`, silently caught by a bare `except Exception`, showing
  "N/A" **every time**, regardless of whether the Blackboard had real data.
- **Fixed**: added `ArgusMemory.get_blackboard_counts()` (real
  `SELECT COUNT(*)` on `targets`/`findings`) and
  `blackboard.get_blackboard_counts()`; `status_bar.py` now calls that
  instead, and the fallback path shows the actual exception instead of a bare
  "N/A" (no more silent failure).

### 3. Knowledge Graph tab was a permanent no-op
- **Broken**: `app/GUI/utils/blackboard.py::build_graph_data()` constructed an
  empty `nx.DiGraph()` and returned it immediately - never queried any real
  data.
- **Why**: stub left over from initial scaffolding (T021), never wired to the
  `targets`/`findings` tables the tactical agent's recon/scanner nodes
  actually populate via `ArgusMemory.upsert_target()`/`add_finding()`.
- **Fixed**: added `ArgusMemory.get_findings_graph_rows()` and rewrote
  `build_graph_data()` to build real domain -> finding nodes/edges from it.

### 4. Dashboard "Recent Activity" and Reports "Generate Report" always empty
- **Broken**: both read `st.session_state.jobs`, initialized to `[]` in
  `dashboard.py` with **nothing anywhere ever appending to it**.
- **Why**: dead state left over from scaffolding; the agent controller writes
  real run data to `logs/agent_runs/agent_<uuid>.json`, never to
  `session_state.jobs`.
- **Fixed**: `overview.py` and `reports.py` now read the real run JSON files
  from `logs/agent_runs/` directly (the same files `AgentController`/
  `run_agent.py` already write and the Agent tab already polls). Reports also
  now maps real finding fields (`tool`/`summary`, no `severity`/`type` keys)
  instead of rendering everything as `?`/info.

### 5. GUI was slow/unresponsive: `time.sleep()` loop froze the whole session
- **Broken**: `app/GUI/tabs/agent.py`'s feed polling was
  `for _ in range(60): ...; time.sleep(1)` inside the main script run.
- **Why**: Streamlit is single-threaded per session. A 60-second blocking
  sleep loop means **no button, no tab switch, nothing** can be processed
  anywhere in the app for up to 60 straight seconds while a run is active -
  this is the direct cause of "GUI is very slow and laggy." It also read the
  same state file twice per iteration (`get_status()` then `get_feed()`,
  which internally calls `get_status()` again).
- **Fixed**: replaced with `st.fragment(run_every="2s")` - only that fragment
  re-executes on a timer; the rest of the page (Start/Stop, navigation) stays
  fully interactive. `run_every` is `None` (no polling at all) when idle.
  Feed/status/results now share a single `get_status()` call per tick.

### 6. (carried over from the recon-stuck investigation) Exploit-probe timeout
- `app/tools/evasion.py::EvasionService.advanced_vuln_probe()` had no explicit
  timeout on its 6 sequential curl probes - see `CHANGELOG.md`'s
  "Fixed: dashboard stuck..." entry for full detail. Directly relevant here
  because it's what let the Agent tab's "Testing / Agent execution" stage
  reach `post_exploit` at all instead of dying at the 600s outer timeout.

### Validation
- `pytest tests/test_gui tests/test_tools tests/test_memory.py` - 79/79 pass.
- Three independent live end-to-end runs against `scanme.nmap.org`
  (see CHANGELOG.md) - the third completed the full
  recon -> scanner -> exploit -> reflective retry loop -> completion with
  `retry_count: 3` and real findings in `final_state`.
