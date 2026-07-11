# Implementation Plan: Agent Prompt System (Canonical)

**Feature ID**: `015-agent-prompt-system` | **Date**: 2026-07-06 | **Spec**: `specs/015-agent-prompt-system/spec.md`

**Status**: Draft

---

## Summary

Fold the rich pentest content of the legacy `app/core/prompts.py` into the modern, state-driven
`app/core/agent/react_prompts.py`, making the latter the single canonical prompt module. Align it
with ADR-13 (structured output), ADR-6 / Constitution VIII (reflective verification), `001` (RAG
context fusion), and `012` section 4/6 (context budget, AI-eval). Deprecate `prompts.py`.

---

## Technical Context

**Language/Version**: Python 3.12.
**Primary Dependencies**: `langchain-core` (message/prompt types), the tool registry, `SecurityReport`
in `app/core/schemas.py`. No new dependency.
**Storage**: none (prompts are pure functions of state).
**Target Platform**: Windows host (production) / any (tests).
**Project Type**: core library module (agent prompt layer).

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Admin-First Elevation | Not Applicable | Pure Python |
| II. Single-Source Installer | Not Applicable | No installer change |
| III. Idempotent & Test-Gated | Compliant | Pure builders; unit-testable |
| IV. Platform-Boundary Clarity | Compliant | No cross-boundary calls |
| V. Observability & Logging | Compliant | Prompt version logged |
| VI. English-Only Documentation | Compliant | ASCII/English prompt text |
| VII. Canonical Authority | Compliant | Establishes one prompt source (012) |
| VIII. Truthful Runtime | Compliant | Preserves reflective-verification mandate |

**Gate Decision**: PASS.

## Project Structure

```text
specs/015-agent-prompt-system/
+-- spec.md
+-- research.md
+-- plan.md
+-- data-model.md
+-- quickstart.md
+-- tasks.md

app/core/agent/react_prompts.py   # canonical (enriched)
app/core/prompts.py               # deprecation shim (Replaced By react_prompts.py)
app/core/schemas.py               # SecurityReport (final-answer contract)
tests/test_agent/test_react_prompts.py   # new unit tests (pure builders)
```

## Key Design Decisions

1. **Merge, not rewrite** (research Decision 1): keep the modern structure; port the methodology,
   reflective verification, and report schema.
2. **Structured output primary** (ADR-13): remove the legacy anti-JSON rule.
3. **Registry-sourced tool names** (research Decision 4): no hard-coded tool lists.
4. **Context fusion + budget** (research Decision 5): STATIC/LIVE separation, live-first budget.
5. **Versioned + evaluated** (research Decision 6): `PROMPT_VERSION` + AI-eval.

## Phases

| Phase | Description | Status | Blocker |
|-------|-------------|--------|---------|
| 0 | Inventory both prompt sources + importers | Done | - |
| 1 | Port methodology + reflective verification + report schema into `react_prompts.py` | Pending | needs pytest |
| 2 | Remove anti-JSON rule; source tool names from registry | Pending | needs pytest |
| 3 | Add STATIC/LIVE fusion sections + context budget | Pending | needs runtime |
| 4 | Add `PROMPT_VERSION`; unit tests (pure builders) | Pending | - |
| 5 | Deprecate `app/core/prompts.py` (shim + warning); repoint `brain.py`; drop unused `format_instructions` | Pending | needs pytest |
| 6 | AI-eval: final answer conforms to `SecurityReport`; loop terminates | Pending | needs Ollama |

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected |
|------|------------|------------------------------|
| Keeping two builder variants (react + prebuilt) | Serves non-tool-calling and tool-calling models | One prompt cannot serve both ReAct-text and native tool_calls |

## Risks & Mitigations

- **Risk**: enriching the prompt changes agent behavior. **Mitigation**: pure-function builders +
  unit tests asserting required sections; AI-eval before deprecating the legacy path.
- **Risk**: `brain.py` still imports `prompts.py`. **Mitigation**: keep the shim re-exporting until
  `brain.py` is repointed and tests pass (Phase 5).
