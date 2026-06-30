# Implementation Plan: GUI Enhancement - Professional Security Dashboard

**Branch**: `011-gui-enhancement` | **Date**: 2026-06-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-gui-enhancement/spec.md`

## Summary

This plan consolidates all existing Argus GUI files (`app/GUI/app.py`, `argus_gui.py`, `desktop_gui.py`) into a single professional Streamlit dashboard with multi-page navigation, LangGraph agent integration, target/session management, knowledge graph visualization, and advanced reporting. The dashboard is launched from `scripts/LAUNCH_STUDIO.bat` with reliable path resolution.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Streamlit, LangGraph, SQLite3, NetworkX, Pyvis, Jinja2, Plotly

**Storage**: SQLite (Blackboard - targets, findings, entities, relations, sessions)

**Testing**: pytest (import validation + component smoke tests)

**Target Platform**: Windows 10/11 + Streamlit web browser

**Project Type**: Web dashboard (Streamlit multi-page app)

**Performance Goals**: Dashboard load < 15s, Knowledge Graph render < 2s for 100 nodes, Agent live feed updates < 1s

**Constraints**: Must work fully offline via Ollama; no external API calls for core functionality; Streamlit session state must handle persistence gracefully.

**Scale/Scope**: Single Streamlit app with 5 tabs, replacing 3 existing GUI files.

## Constitution Check

- **I. Admin-First Elevation**: N/A for GUI (launcher handles environment checks).
- **II. Single-Source Installer**: N/A.
- **III. Idempotent & Test-Gated**: The dashboard is stateless on disk except for intentional session save/load via Blackboard.
- **IV. Platform-Boundary Clarity**: GUI runs on Windows host. Agent tool execution goes through WSL bridge — no direct Kali calls from GUI.
- **V. Observability & Logging**: All GUI operations logged to `logs/gui_<timestamp>.log`. Agent feed displayed live in UI.
- **VI. English-Only Documentation**: Verified. All UI strings, logs, and docstrings in English.

## Project Structure

### Documentation (this feature)

```text
specs/011-gui-enhancement/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Technical research findings
├── data-model.md        # Data entities and relationships
├── quickstart.md        # Validation scenarios
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
app/GUI/
├── __init__.py
├── app.py               # DEPRECATED - legacy entry point, aliased to dashboard
├── argus_gui.py         # DEPRECATED - legacy entry point, aliased to dashboard
├── desktop_gui.py       # KEPT - standalone Tkinter fallback (no changes)
├── studio.py            # KEPT - alias for backward compatibility
├── dashboard.py         # NEW - Main unified Streamlit dashboard
├── pages/
│   ├── __init__.py
│   ├── dashboard.py     # NEW - Overview tab (stats, status cards, recent activity)
│   ├── targets.py       # NEW - Target management tab
│   ├── agent.py         # NEW - LangGraph agent control + live feed
│   ├── reports.py       # NEW - Report generation + export
│   ├── knowledge_graph.py # NEW - Interactive entity-relationship graph
│   └── settings.py      # NEW - Configuration panel
├── components/
│   ├── __init__.py
│   ├── status_bar.py    # NEW - System status indicator
│   ├── session_manager.py # NEW - Session save/load logic
│   └── export.py        # NEW - Report export engine
├── utils/
│   ├── __init__.py
│   ├── blackboard.py    # NEW - Blackboard query helpers
│   └── agent_controller.py # NEW - LangGraph agent wrapper
└── static/
    └── style.css        # NEW - Custom styling

scripts/
└── LAUNCH_STUDIO.bat    # UPDATED - fixed path resolution

tests/
└── test_gui/
    ├── test_imports.py  # EXISTING - updated
    └── test_dashboard.py # NEW - dashboard smoke tests
```

**Structure Decision**: Single Streamlit app using native multi-page pattern (`pages/` directory). Components and utilities separated for testability. No backend API needed — Streamlit session state + direct Python calls to core services.

## Complexity Tracking

No violations. The multi-page pattern is the recommended Streamlit structure and keeps complexity low while supporting all 5 user stories.
