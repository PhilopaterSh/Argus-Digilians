# Implementation Plan: Tactical Modules Refactoring

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-29 | **Spec**: `specs/006-tactical-modules/spec.md`

---

## Summary

Refactor all 9 Python modules in `app/modules/` to use valid `app.core.*` imports, introduce a `BaseTacticalModule` abstract class with a strategy pattern, and add import-validation smoke tests. No functionality changes — only structural cleanup.

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: None new — existing `app.tools.tool_registry`, `app.core.brain`, `app.core.memory`

**Storage**: N/A

**Testing**: pytest — import validation + smoke tests

**Target Platform**: Windows 10/11 + WSL2 (Kali)

**Project Type**: Library module (tactical orchestration layer)

**Performance Goals**: None (structural refactor)

**Constraints**: Must not change runtime behavior of any module

**Scale/Scope**: 9 Python files, ~450 LOC, 1 new file (`base.py`)

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Admin-First Elevation | ✅ Not Applicable | Pure Python refactor |
| II. Single-Source Installer | ✅ Not Applicable | No installer changes |
| III. Idempotent & Test-Gated | ✅ Compliant | No side effects |
| IV. Platform-Boundary Clarity | ✅ Compliant | All modules already use WSL bridge |
| V. Observability & Logging | ✅ Existing | Modules use print() — acceptable for now |
| VI. English-Only Documentation | ✅ Compliant | All names and docs in English |

**Gate Decision**: PASS.

---

## Project Structure

### Documentation

```text
specs/006-tactical-modules/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── BaseTacticalModule.md
└── tasks.md
```

### Source Code

```text
app/modules/
├── __init__.py       # Refactored: run_all(), module registry
├── base.py           # New: BaseTacticalModule ABC
├── argus_reasoning.py
├── argus_deep_exploit.py
├── stealth_exploit.py
├── run_recon.py
├── run_full_recon.py
├── map_target.py
├── seed_memory.py
├── ddgs.py
├── crawler.py
└── check_subs.sh     # Shell script — stays as-is

tests/
└── test_modules/
    └── test_imports.py   # Import validation for all 9 modules
```
