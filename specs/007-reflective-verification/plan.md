# Implementation Plan: Reflective Verification Hardening

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-29 | **Spec**: `specs/007-reflective-verification/spec.md`

---

## Summary

Harden `ReflectiveVerificationService` (188 LOC, 3 methods) by implementing the infinite-loop prevention TODO, exposing all 3 methods as LangChain-compatible tools via `WSLBridgeTools`, and adding comprehensive test coverage.

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: ArgusMemory (Phase 003), re, json (stdlib)

**Storage**: Blackboard (SQLite) for command history tracking

**Testing**: pytest — 4 test files

**Target Platform**: Windows 10/11 + WSL2 (Kali)

**Project Type**: Library module (verification service)

**Performance Goals**: pre_execute_verify < 50ms; post_execute_verify < 100ms

**Constraints**: Must remain backward-compatible with existing callers

**Scale/Scope**: 1 file hardened, 2-3 new methods, 1 test file

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I-VI | ✅ All Pass | No new concerns |

**Gate Decision**: PASS.

---

## Project Structure

```text
specs/007-reflective-verification/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ReflectiveVerificationService.md
└── tasks.md

app/tools/
└── reflective_verification.py  # Hardened

tests/test_tools/
└── test_reflective_verification.py
```
