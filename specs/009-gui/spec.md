# Feature Specification: GUI Alignment & Tkinter Desktop

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-29

**Status**: Implemented — **Primary UI Superseded By** `011-gui-enhancement` (the unified Streamlit "Argus Studio" dashboard, `app/GUI/dashboard.py`, is the canonical primary UI per `012` §2.5). **Retained** from this spec: the import-path fixes and `app/GUI/desktop_gui.py` (Tkinter) as an **optional lightweight fallback** for environments without Streamlit. Do not build two competing primary UIs.

**Input**: Two Streamlit apps exist (`app/GUI/app.py` and `app/GUI/argus_gui.py`) but the architecture doc references Tkinter desktop, `gui_app.py`, and `studio.py` — none of which exist. `argus_gui.py` uses broken legacy imports (`from core.tools`).

---

## User Scenarios & Testing

### User Story 1 - Fix Legacy Imports (Priority: P1)

As a developer, I want all GUI files to use valid `app.core.*` and `app.tools.*` imports, so the GUI can be launched from any directory.

**Acceptance Scenarios**:
1. Given `app/GUI/argus_gui.py`, When imported, Then all imports resolve to `app.*` paths.
2. Given both GUI files, When `python -c "import app.GUI.app"` runs, Then no ImportError.

### User Story 2 - Desktop Tkinter GUI (Priority: P2)

As a user, I want a lightweight Tkinter desktop interface (as described in the architecture doc) for environments where Streamlit is unavailable.

**Acceptance Scenarios**:
1. Given Tkinter installed, When `python app/GUI/desktop_gui.py` runs, Then a window appears with target input and run button.
2. Given no Tkinter, When ran, Then a clear error suggests installing `python3-tk`.

### User Story 3 - Test Coverage (Priority: P3)

As a developer, I want import validation tests for GUI files.

---

## Requirements

- **FR-001**: Fix import paths in `argus_gui.py`.
- **FR-002**: Create `app/GUI/desktop_gui.py` — Tkinter desktop app matching architecture doc.
- **FR-003**: Create `app/GUI/studio.py` — alias/module for `app.py`.
- **FR-004**: Import-validation tests for GUI modules.

## Key Entities

- `app/GUI/app.py` — no changes
- `app/GUI/argus_gui.py` — fix imports
- `app/GUI/desktop_gui.py` — NEW: Tkinter desktop
- `app/GUI/studio.py` — NEW: alias
- `tests/test_gui/test_imports.py` — import validation
