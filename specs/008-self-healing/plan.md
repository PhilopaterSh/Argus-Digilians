# Implementation Plan: Self-Healing Expansion

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-29 | **Spec**: `specs/008-self-healing/spec.md`

---

## Summary

Expand `SelfHealingService` from 31 lines (pip/apt install only) to a proactive health monitor with service health checks, automated restart for WSL/Ollama/Python services, and config repair capabilities. Register all new methods in `WSLBridgeTools`.

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: subprocess, sys, os (stdlib) — no new packages

**Storage**: N/A (runtime checks only)

**Testing**: pytest — mock subprocess calls

**Target Platform**: Windows 10/11 + WSL2 (Kali)

**Project Type**: Library module (self-healing service)

**Performance Goals**: health_check < 2s (parallel checks); restart < 10s

**Constraints**: Must not hang on unresponsive services (add timeouts)

**Scale/Scope**: 1 file expanded from 31 → ~150 LOC, 1 test file

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I-VI | ✅ All Pass | No elevation needed (checks use existing bridge) |

**Gate Decision**: PASS.

---

## Project Structure

```text
specs/008-self-healing/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── SelfHealingService.md
└── tasks.md

app/tools/
└── self_heal.py    # Expanded

tests/test_tools/
└── test_self_heal.py
```
