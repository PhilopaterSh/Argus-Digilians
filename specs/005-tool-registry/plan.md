# Implementation Plan: Tool Registry Abstraction & Testing

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-29 | **Spec**: `specs/005-tool-registry/spec.md`

**Input**: Feature specification from `specs/005-tool-registry/spec.md`

---

## Summary

Introduce a plugin-based `ToolRegistry` with `BaseToolService` abstract class, refactor the existing `WSLBridgeTools` facade to use it (backward-compatibly), and create the missing `brain_v2.py` and `agent_factory_v2.py` components referenced in the architecture document. Add full test coverage for registry patterns.

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: None new — uses existing `app/tools/*.py` services, `app/core/memory/`, `abc` (stdlib)

**Storage**: N/A (in-memory registry; persistence handled by blackboard)

**Testing**: pytest (existing `tests/` directory)

**Target Platform**: Windows 10/11 + WSL2 (Kali)

**Project Type**: Library module (core abstraction layer)

**Performance Goals**: Tool registration < 10ms; tool lookup < 1ms

**Constraints**: Must be backward-compatible with existing `WSLBridgeTools` API surface (42 public methods/properties)

**Scale/Scope**: 14 sub-services to adapt, 2 new modules (`app/core/registry/`, `app/core/agent/`), 3 new test files

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Admin-First Elevation | ✅ Not Applicable | Pure Python abstraction; no OS changes |
| II. Single-Source Installer | ✅ Not Applicable | No installer changes |
| III. Idempotent & Test-Gated | ✅ Compliant | Registry is stateless in-memory |
| IV. Platform-Boundary Clarity | ✅ Compliant | All tools delegate to WSL via existing bridge |
| V. Observability & Logging | ⚠️ Needs Work | Add logging to registry operations |
| VI. English-Only Documentation | ✅ Compliant | All names and docs in English |

**Gate Decision**: PASS — no violations requiring Complexity Tracking.

---

## Project Structure

### Documentation (this feature)

```text
specs/005-tool-registry/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── BaseToolService.md
│   ├── ToolRegistry.md
│   ├── ArgusBrainV2.md
│   └── AgentFactory.md
└── tasks.md
```

### Source Code (repository root)

```text
app/core/registry/
├── __init__.py
├── base_tool.py          # BaseToolService ABC
└── tool_registry.py       # ToolRegistry class

app/core/agent/
├── __init__.py
├── brain_v2.py            # ArgusBrainV2 with registry dispatch
└── agent_factory_v2.py    # Factory functions

app/tools/
└── tool_registry.py       # Refactored WSLBridgeTools → uses ToolRegistry internally

tests/
├── test_registry/
│   ├── test_base_tool.py
│   ├── test_tool_registry.py
│   └── test_brain_v2.py
```

**Structure Decision**: New `app/core/registry/` follows same pattern as `app/core/memory/` (Phase 003). New `app/core/agent/` is the canonical location for brain/agent code per Architecture v2. Existing `app/tools/tool_registry.py` is refactored in place for backward compatibility.

---

## Complexity Tracking

No constitution violations — Complexity Tracking table is not required.

---

## Alignment with Architecture Vision

| Architecture Component | Implementation |
|------------------------|----------------|
| Tool Registry (§5.1) | `app/core/registry/tool_registry.py` — `ToolRegistry` class |
| BaseToolService (new) | `app/core/registry/base_tool.py` — abstract base |
| Brain V2 (§3.1) | `app/core/agent/brain_v2.py` — `ArgusBrainV2` |
| Agent Factory (new) | `app/core/agent/agent_factory_v2.py` |
| Legacy Facade (§5.1) | `app/tools/tool_registry.py` — refactored `WSLBridgeTools` |
