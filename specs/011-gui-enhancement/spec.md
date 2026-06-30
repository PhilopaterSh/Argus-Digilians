# Feature Specification: GUI Enhancement - Professional Security Dashboard

**Feature Branch**: `011-gui-enhancement`

**Created**: 2026-06-30

**Status**: Draft

**Input**: User description: "تحسين واجهة المستخدم الرسومية وجعلها منصة احترافية متكاملة تطلق من LAUNCH_STUDIO.bat مع دعم الـ LangGraph Agent وجميع خدمات Argus."

## User Scenarios & Testing

### User Story 1 - Unified Professional Dashboard (Priority: P1)

As a security researcher, I want a single, professional web-based dashboard that replaces all existing fragmented GUIs (`app.py`, `argus_gui.py`) and launches reliably from `scripts/LAUNCH_STUDIO.bat`, so I can manage all pentest operations from one place.

**Why this priority**: The current fragmented GUIs have inconsistent UX, duplicate code, and path resolution issues in the launcher. Users need a single entry point.

**Independent Test**: Can be tested by running `LAUNCH_STUDIO.bat` from the repo root, verifying the Streamlit dashboard loads at `http://localhost:12199` with all functional tabs present (Dashboard, Targets, Agent, Reports, Settings).

**Acceptance Scenarios**:
1. **Given** `scripts/LAUNCH_STUDIO.bat`, **When** executed from any directory, **Then** it resolves all paths correctly and launches the Streamlit dashboard.
2. **Given** the unified dashboard, **When** it loads, **Then** it shows a sidebar with navigation tabs: Dashboard, Targets, Agent Live Feed, Reports, Settings.
3. **Given** the dashboard, **When** a user clicks any tab, **Then** the corresponding view loads without page refresh (multi-page structure).

---

### User Story 2 - LangGraph Agent Integration (Priority: P1)

As a user, I want to see the LangGraph penetration testing agent running in real-time within the dashboard, with live node transitions, state visualization, and the ability to start/stop/pause operations.

**Why this priority**: The 010-langgraph-agent feature built the agent but there is no GUI to interact with it. The GUI must provide the control interface.

**Independent Test**: Can be tested by launching the agent from the GUI against a test target and observing live node transitions (Recon → Scanner → Exploit → Reflective → Post-Exploit) in the agent feed panel.

**Acceptance Scenarios**:
1. **Given** a target entered in the Agent tab, **When** the user clicks "Start Agent", **Then** the LangGraph agent executes and each node transition is displayed as a live card in the feed.
2. **Given** an active agent run, **When** the Reflective Node detects a WAF block, **Then** the GUI shows the retry loop with payload modification status.
3. **Given** the agent completes, **When** findings are persisted, **Then** the Dashboard tab updates statistics and findings count.

---

### User Story 3 - Target & Session Management (Priority: P2)

As a security researcher, I want to manage multiple targets, save/load sessions, and view target history so I can organize my pentest campaigns effectively.

**Why this priority**: The current GUI handles only one target at a time with no persistence. Managing complex assessments requires session management.

**Independent Test**: Can be tested by adding 3 targets, saving the session, closing the browser, reopening, and verifying all targets are listed.

**Acceptance Scenarios**:
1. **Given** the Targets tab, **When** a user adds a new target (URL/IP/domain), **Then** it appears in the target list with status "pending".
2. **Given** an active session, **When** the user clicks "Save Session", **Then** the session state is persisted to SQLite Blackboard and can be loaded on next launch.
3. **Given** a saved session, **When** the user loads it, **Then** all previous targets, findings, and agent state are restored.

---

### User Story 4 - Knowledge Graph Visualization (Priority: P2)

As a security analyst, I want to visually explore the relationships between targets, findings, entities, and infrastructure in an interactive graph view.

**Why this priority**: The SQLite Blackboard stores entities and relations but there is no visual interface to explore the knowledge graph.

**Independent Test**: Can be tested by running recon on a target, then navigating to the Knowledge Graph tab and seeing nodes (domain, IP, technologies, vulnerabilities) with edges between them.

**Acceptance Scenarios**:
1. **Given** findings exist in the Blackboard, **When** the user opens the Knowledge Graph tab, **Then** entities are displayed as interactive nodes with connections.
2. **Given** a knowledge graph, **When** the user clicks a node, **Then** details about that entity (type, properties, related findings) are shown.
3. **Given** a graph with many nodes, **When** the user searches/filters, **Then** irrelevant nodes are hidden.

---

### User Story 5 - Advanced Reporting (Priority: P3)

As a security consultant, I want to export professional penetration test reports in multiple formats (HTML, PDF, Markdown, JSON) with structured findings, evidence, and risk scores.

**Why this priority**: The current download button only exports raw Markdown. Professional engagements require structured, branded reports.

**Independent Test**: Can be tested by running a full analysis, clicking "Export Report", selecting HTML format, and verifying the generated file contains all findings with proper formatting.

**Acceptance Scenarios**:
1. **Given** completed findings, **When** the user clicks "Export Report", **Then** format options appear (HTML/PDF/MD/JSON).
2. **Given** HTML format selected, **When** exported, **Then** the file includes executive summary, findings table, technical details, and risk scores.
3. **Given** JSON format selected, **When** exported, **Then** the file is valid JSON parseable by external tools.

---

### Edge Cases

- What happens when Streamlit crashes mid-session? Auto-recovery with session restore.
- How does the GUI handle Ollama being down? Graceful degradation with clear status indicator.
- How does the Knowledge Graph handle 1000+ nodes? Pagination, clustering, and search.
- What happens when the LangGraph agent runs indefinitely? Configurable timeout with kill switch.
- How does the GUI behave on low-resolution screens? Responsive layout adapts to viewport.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a single Streamlit dashboard accessible via `LAUNCH_STUDIO.bat` that consolidates all GUI views.
- **FR-002**: `LAUNCH_STUDIO.bat` MUST resolve all paths correctly regardless of the current working directory.
- **FR-003**: System MUST integrate with the LangGraph agent (`app/core/agent/graph.py`) for live agent control and monitoring.
- **FR-004**: System MUST display live agent node transitions in real-time using Streamlit status/streaming components.
- **FR-005**: System MUST support adding, removing, and selecting multiple targets from a target list.
- **FR-006**: System MUST persist sessions (targets, findings, agent state) to SQLite Blackboard.
- **FR-007**: System MUST provide an interactive knowledge graph visualization using Pyvis/VisJS showing entities, relations, and findings.
- **FR-008**: System MUST support report export in HTML, Markdown, and JSON formats.
- **FR-009**: System MUST provide a settings panel to configure model name, Ollama endpoint, SSH credentials, and theme.
- **FR-010**: System MUST display real-time system status (Ollama online/offline, WSL bridge, SSH, Blackboard size).
- **FR-011**: System MUST provide a job/task queue showing running, completed, and failed operations.
- **FR-012**: System MUST log all operations with timestamps accessible from a Logs tab.
- **FR-013**: The old `app/GUI/app.py` and `app/GUI/argus_gui.py` MUST be deprecated in favor of the new dashboard, aliased for backward compatibility.

### Key Entities

- **Dashboard**: The main Streamlit app (`app/GUI/dashboard.py`) with multi-page navigation.
- **Target Manager**: Session-persisted target list with status tracking.
- **Agent Controller**: Live interface to LangGraph agent with start/stop/status.
- **Knowledge Graph**: Visual entity-relationship graph from Blackboard data.
- **Report Generator**: Multi-format export engine for pentest findings.
- **Settings Store**: Config persisted to `config.yaml` for GUI settings.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `LAUNCH_STUDIO.bat` launches the dashboard successfully from any directory in under 15 seconds.
- **SC-002**: Users can complete a full pentest workflow (add target → run LangGraph agent → view findings → export report) without switching to CLI.
- **SC-003**: Knowledge Graph renders 100+ entity nodes with sub-2 second load time.
- **SC-004**: Sessions are saved and restored with 100% accuracy (same targets, findings, state).
- **SC-005**: All 5 tabs (Dashboard, Targets, Agent, Reports, Settings) are functional with zero import errors.

## Assumptions

- Streamlit and its dependencies are installed in `Argus_venv`.
- Ollama is accessible at `localhost:11434` (configurable).
- SQLite Blackboard database exists and is accessible.
- LangGraph agent code from 010-langgraph-agent is implemented and importable.
- The user has a modern web browser (Chrome/Firefox/Edge) for the dashboard.
- NetworkX and Pyvis are available for knowledge graph visualization (installable via pip).
