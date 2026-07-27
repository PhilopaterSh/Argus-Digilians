# Implementation Plan: GUI Alignment & Tkinter Desktop

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-29 | **Spec**: `specs/009-gui/spec.md`

---

## Summary

Fix broken imports in `argus_gui.py`, create the missing `desktop_gui.py` (Tkinter) and `studio.py` referenced in the architecture document, and add import-validation tests for all GUI modules.

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: streamlit (existing), tkinter (stdlib)

**Storage**: N/A

**Testing**: pytest — import validation only

**Target Platform**: Windows 10/11 (GUI host)

**Project Type**: Desktop GUI (Tkinter) + Web UI (Streamlit)

**Performance Goals**: N/A

**Constraints**: Tkinter is optional — fail gracefully if not installed

**Scale/Scope**: 2 files fixed, 2 new files, 1 test file

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I-VI | ✅ All Pass | No elevation needed |

**Gate Decision**: PASS.

---

## Project Structure

```text
specs/009-gui/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── GUI.md
└── tasks.md

app/GUI/
├── __init__.py
├── app.py          # Streamlit (no changes)
├── argus_gui.py    # Fix imports
├── desktop_gui.py  # NEW: Tkinter desktop
├── studio.py       # NEW: alias for app.py
├── Launch_Argus.bat
└── Run_Argus_Studio.bat

tests/test_gui/
└── test_imports.py
```
