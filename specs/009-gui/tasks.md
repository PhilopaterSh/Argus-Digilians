---

description: "Task list for GUI Alignment & Tkinter Desktop"
---

# Tasks: GUI Alignment & Tkinter Desktop

---

## Phase 1: US1 — Fix Legacy Imports (Priority: P1)

- [ ] T001 Fix imports in `app/GUI/argus_gui.py` (`core.tools` → `app.tools.tool_registry`, `core.agent` → `app.core.brain`)

---

## Phase 2: US2 — Desktop Tkinter GUI (Priority: P2)

- [ ] T002 Create `app/GUI/desktop_gui.py` with Tkinter desktop interface
- [ ] T003 Create `app/GUI/studio.py` as alias/re-export for `app.py`

---

## Phase 3: US3 — Import Validation Tests (Priority: P3)

- [ ] T004 Create `tests/test_gui/test_imports.py` with import validation tests

---

## Phase 4: Polish

- [ ] T005 Run test suite + verify all imports + commit
