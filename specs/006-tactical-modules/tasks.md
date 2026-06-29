---

description: "Task list for Tactical Modules Refactoring"
---

# Tasks: Tactical Modules Refactoring

**Input**: Design documents from `specs/006-tactical-modules/`

**Prerequisites**: plan.md, spec.md, research.md, contracts/

---

## Phase 1: Setup

- [ ] T001 Create `app/modules/base.py` with `BaseTacticalModule` ABC

---

## Phase 2: US1 — Fix Import Paths (Priority: P1)

**Goal**: All 9 modules use valid `app.*` imports

- [ ] T002 [US1] Fix imports in `app/modules/argus_reasoning.py` (`core.agent` → `app.core.brain`, `core.tools` → `app.tools.tool_registry`)
- [ ] T003 [US1] Fix imports in `app/modules/argus_deep_exploit.py` (`core.tools` → `app.tools.tool_registry`)
- [ ] T004 [US1] Fix imports in `app/modules/run_recon.py` (`core.tools` → `app.tools.tool_registry`)
- [ ] T005 [US1] Fix imports in `app/modules/run_full_recon.py` (`core.tools` → `app.tools.tool_registry`)
- [ ] T006 [US1] Fix imports in `app/modules/map_target.py` (`core.tools` → `app.tools.tool_registry`)
- [ ] T007 [US1] Fix imports in `app/modules/crawler.py` (`core.tools` → `app.tools.tool_registry`)

---

## Phase 3: US2 — BaseTacticalModule Interface (Priority: P2)

**Goal**: Common interface + orchestrator

- [ ] T008 [US2] Implement `BaseTacticalModule` in `app/modules/base.py` with `name`, `description`, `execute(target)` 
- [ ] T009 [US2] Refactor `app/modules/__init__.py` with `register()`, `run_all()`, `run_module()`, `list_modules()`

---

## Phase 4: US3 — Import Validation Tests (Priority: P2)

**Goal**: Smoke tests verifying all modules import cleanly

- [ ] T010 [P] [US3] Create `tests/test_modules/` directory with `__init__.py`
- [ ] T011 [US3] Write import validation test for all 9 modules in `tests/test_modules/test_imports.py`

---

## Phase 5: Polish

- [ ] T012 Run import validation + test suite
