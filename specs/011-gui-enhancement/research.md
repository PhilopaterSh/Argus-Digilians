# Research: GUI Enhancement Technical Decisions

## Decision 1: Streamlit Multi-Page Architecture

**Decision**: Use Streamlit's native `pages/` directory pattern instead of `st.navigation` or custom routing.

**Rationale**: Streamlit's `pages/` auto-discovery provides zero-config multi-page navigation. Each page is a separate `.py` file in `pages/`, and Streamlit handles sidebar navigation automatically. This is simpler, more maintainable, and better documented than custom solutions.

**Alternatives considered**:
- Custom `st.navigation` with `st.Page`: Newer API but less stable, requires Streamlit >= 1.36.
- Single-file with conditional rendering: Becomes unmaintainable beyond 3-4 views.

## Decision 2: Knowledge Graph with Pyvis

**Decision**: Use Pyvis (Python wrapper for VisJS) for interactive graph visualization.

**Rationale**: Pyvis generates self-contained HTML with VisJS, works offline, handles 1000+ nodes, and supports click/drag/zoom with zero external dependencies at runtime.

**Alternatives considered**:
- Plotly Graph Objects: Good but requires network for CDN resources.
- D3.js manually: Too complex for the value gained.
- NetworkX + Matplotlib: Static only, no interactivity.

## Decision 3: Session Persistence via Blackboard (SQLite)

**Decision**: Store session state in the existing SQLite Blackboard under a new `sessions` table.

**Rationale**: The Blackboard already exists and is the canonical data store. Adding a `sessions` table avoids introducing a new persistence mechanism. Sessions store: target list, agent state snapshots, settings overrides, and active findings.

**Alternatives considered**:
- Streamlit session state only: Lost on browser refresh.
- JSON files on disk: Prone to corruption, no query capability.
- New SQLite database: Unnecessary duplication.

## Decision 4: Report Generation with Jinja2

**Decision**: Use Jinja2 templates for HTML report generation, with Markdown fallback for simple exports.

**Rationale**: Jinja2 produces professional, branded HTML reports with customizable templates. Markdown is simpler but limited. JSON export uses Python's `json` module directly.

**Alternatives considered**:
- WeasyPrint for PDF: Heavy dependency, complex CSS.
- ReportLab: Too low-level for this use case.
- FPDF: Limited formatting capabilities.
- pdfkit (wkhtmltopdf): Requires external binary, problematic on Windows.

## Decision 5: Agent Integration via Subprocess + State File

**Decision**: Launch the LangGraph agent as a subprocess and monitor its progress via a shared state file (JSON) updated by the agent.

**Rationale**: The LangGraph agent is a long-running process. Running it in the same Streamlit process would block the UI. Subprocess with periodic state file reads allows non-blocking live updates.

**Alternatives considered**:
- Direct import + threading: Complex, risk of GIL blocking Streamlit.
- WebSocket + asyncio: Streamlit doesn't natively support WebSocket streaming (requires custom component).
- Redis pub/sub: Overkill for a local-only tool.
