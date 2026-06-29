# Feature Specification: Tactical Modules Refactoring

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-29

**Status**: Draft

**Input**: The `app/modules/` directory contains 10 tactical workflow files (`argus_reasoning.py`, `argus_deep_exploit.py`, `stealth_exploit.py`, `run_recon.py`, `run_full_recon.py`, `map_target.py`, `seed_memory.py`, `ddgs.py`, `crawler.py`, `check_subs.sh`) using legacy flat import paths (`from core.xxx`) instead of the new `app.core.xxx` structure. No shared base class or strategy pattern exists.

---

## User Scenarios & Testing

### User Story 1 - Clean Imports (Priority: P1)

As a developer, I want all tactical modules to use valid imports matching the new project structure, so they can be imported and tested without PYTHONPATH hacks.

**Acceptance Scenarios**:
1. Given `app/modules/argus_reasoning.py`, When imported, Then it resolves all imports from `app.core.*` and `app.tools.*`.
2. Given all 9 Python files, When `pytest --import-mode=importlib` runs, Then zero ImportErrors occur.

### User Story 2 - BaseTacticalModule Interface (Priority: P2)

As a developer, I want a common interface for all tactical modules, so new workflows can be added without duplicating boilerplate.

**Acceptance Scenarios**:
1. Given `BaseTacticalModule`, When subclassed, Then `execute(target)` must be implemented.
2. Given a list of modules, When `run_all()` is called, Then each module executes sequentially.

### User Story 3 - Test Coverage (Priority: P2)

As a developer, I want at least smoke tests for each module that verify clean import and basic execution path.

---

## Requirements

- **FR-001**: Fix import paths in all 9 `.py` files from `from core.xxx` to `from app.core.xxx`.
- **FR-002**: `BaseTacticalModule` abstract class in `app/modules/base.py`.
- **FR-003**: Each module either implements `BaseTacticalModule` or is wrapped.
- **FR-004**: `run_all()` orchestrator in `app/modules/__init__.py`.
- **FR-005**: All modules pass import validation in CI.

## Key Entities

- `app/modules/base.py` — `BaseTacticalModule`
- `app/modules/__init__.py` — `run_all()`, module registry
- `app/modules/*.py` — 9 refactored files
