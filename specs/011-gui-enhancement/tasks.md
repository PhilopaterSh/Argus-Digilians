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
