# Tasks: GUI Enhancement - Professional Security Dashboard

**Input**: Design documents from `/specs/011-gui-enhancement/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup & Foundation

**Purpose**: Project initialization, path fixes, and shared utilities

- [ ] T001 [P] Fix `scripts/LAUNCH_STUDIO.bat`: update path to resolve `app/GUI/dashboard.py` correctly from any working directory; add `PYTHONPATH` set; add check for virtual environment
- [ ] T002 [P] Create `app/GUI/pages/__init__.py`, `app/GUI/components/__init__.py`, `app/GUI/utils/__init__.py` package structure
- [ ] T003 [P] Create `app/GUI/utils/blackboard.py`: helper module with functions `load_targets()`, `save_target()`, `load_findings()`, `load_entities()`, `load_relations()` wrapping `ArgusMemory`
- [ ] T004 [P] Create `app/GUI/components/status_bar.py`: reusable Streamlit component showing Ollama status, WSL/SSH bridge status, Blackboard stats (targets, findings count)
- [ ] T005 Add `gui_sessions` and `gui_jobs` tables to Blackboard schema in `app/core/memory/memory_service.py`

---

## Phase 2: User Story 1 - Unified Professional Dashboard (Priority: P1) 🎯 MVP

**Goal**: Single multi-page Streamlit dashboard that replaces all existing GUIs

- [ ] T006 Create `app/GUI/dashboard.py` as the main entry point with:
  - Multi-page navigation sidebar (Dashboard, Targets, Agent, Reports, Settings)
  - Global status bar component at top
  - Session state initialization for targets, jobs, settings
  - Dark theme with terminal-style aesthetics
- [ ] T007 [P] Create `app/GUI/pages/dashboard.py` with:
  - Statistics cards (total targets, findings, active jobs, last run)
  - Recent activity feed (last 10 operations with timestamps)
  - Quick action buttons (New Target, Start Agent, Generate Report)
  - System health overview (Ollama: online/offline, WSL: active/inactive, Model: name)
- [ ] T008 [P] Create `app/GUI/pages/settings.py` with:
  - Model selection dropdown (reads available Ollama models)
  - Ollama endpoint URL input (default: localhost:11434)
  - SSH credentials (username, password/host)
  - Theme selector (dark/light)
  - Session save/load controls
  - Log viewer (stream `logs/gui_*.log`)
- [ ] T009 [P] Create `app/GUI/static/style.css` with custom dark terminal theme matching Argus branding
- [ ] T010 Update `app/GUI/__init__.py` to export key classes from dashboard for backward compatibility
- [ ] T011 Run import validation: `python -c "from app.GUI.dashboard import *"` — zero errors

---

## Phase 3: User Story 2 - LangGraph Agent Integration (Priority: P1)

**Goal**: Live agent control interface with real-time node transition visualization

- [ ] T012 [P] Create `app/GUI/utils/agent_controller.py` with:
  - `AgentController` class wrapping LangGraph agent (`app/core/agent/graph.py`)
  - `start(target, options)` — launches agent as subprocess with state file
  - `stop()` — kills agent subprocess
  - `get_status()` — reads agent state file for current node, progress, errors
  - `get_feed()` — returns list of events since last poll
- [ ] T013 Create `app/GUI/pages/agent.py` with:
  - Target selector dropdown (from session targets)
  - Start/Stop/Pause buttons
  - Live agent feed panel showing node transitions as styled cards
  - Current state display (active node, elapsed time, retry count)
  - Final results panel showing structured findings on completion
  - Error log expandable section
- [ ] T014 Create agent event-based logging: agent writes JSON events to a shared log file; dashboard polls and renders them
- [ ] T015 Test: Run agent from GUI, verify live feed shows all node transitions

---

## Phase 4: User Story 3 - Target & Session Management (Priority: P2)

**Goal**: Multi-target management with persistent sessions

- [ ] T016 [P] Create `app/GUI/pages/targets.py` with:
  - "Add Target" form (URL/domain/IP with type selector)
  - Target list table (name, type, status, added date, tags)
  - Bulk actions (select multiple → run agent, delete, export)
  - Search/filter bar
  - Target detail panel (expandable: findings summary, last scan date)
- [ ] T017 [P] Create `app/GUI/components/session_manager.py` with:
  - `save_session()` — persists current targets, settings, agent state to SQLite
  - `load_session(session_id)` — restores full state from SQLite
  - `list_sessions()` — returns saved sessions with metadata
  - `delete_session(session_id)` — removes session
- [ ] T018 Wire session save/load to Settings page and auto-save on target changes
- [ ] T019 Test: Add 3 targets, save session, reload — verify all targets restored

---

## Phase 5: User Story 4 - Knowledge Graph Visualization (Priority: P2)

**Goal**: Interactive entity-relationship graph from Blackboard data

- [ ] T020 Create `app/GUI/pages/knowledge_graph.py` with:
  - Pyvis interactive graph rendered in Streamlit via HTML component
  - Nodes: targets (red), IPs (blue), technologies (green), vulnerabilities (orange), findings (gray)
  - Edges: labeled relationships (HOSTS, RUNS, HAS_VULN, DISCOVERED_BY)
  - Click node → show entity details panel
  - Search/filter by entity name or type
  - Zoom controls + reset view button
  - Export graph as HTML file
- [ ] T021 Create helper `build_graph_data()` in `app/GUI/utils/blackboard.py` that queries entities + relations and returns NetworkX graph
- [ ] T022 Test: Run recon, verify knowledge graph renders with entities and connections

---

## Phase 6: User Story 5 - Advanced Reporting (Priority: P3)

**Goal**: Professional report export in multiple formats

- [ ] T023 [P] Create `app/GUI/components/export.py` with:
  - `generate_html_report(findings, target, template)` — Jinja2-based HTML report with executive summary, findings table, technical details, risk matrix
  - `generate_markdown_report(findings, target)` — Structured markdown with sections
  - `generate_json_report(findings, target)` — Valid JSON for external tools
  - `get_available_templates()` — lists report templates from `templates/reports/`
- [ ] T024 Create `app/GUI/pages/reports.py` with:
  - Session/target selector for report scope
  - Format selector (HTML/MD/JSON)
  - Template selector (if HTML)
  - "Generate" button with progress indicator
  - Download button after generation
  - Report history table (past reports with regenerate option)
- [ ] T025 Create Jinja2 report template `app/GUI/templates/reports/default.html` with professional styling
- [ ] T026 Test: Generate HTML report, verify it contains executive summary, all findings, risk scores

---

## Phase 7: Polish & Cross-Cutting

**Purpose**: Tests, documentation, backward compatibility

- [ ] T027 [P] Create `tests/test_gui/test_dashboard.py`: smoke tests for all pages (import validation + render test)
- [ ] T028 [P] Create `tests/test_gui/test_session.py`: session save/load round-trip tests
- [ ] T029 [P] Update `app/GUI/app.py` and `app/GUI/argus_gui.py` to show deprecation warning and redirect to dashboard
- [ ] T030 [P] Run full test suite: `pytest tests/test_gui/ -v` — all pass
- [ ] T031 Commit all changes with message: `feat(gui): 011 - professional security dashboard + LangGraph integration + session management + knowledge graph + reporting`

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
