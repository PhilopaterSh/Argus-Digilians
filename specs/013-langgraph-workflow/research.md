# Research: LangGraph Workflow + JSON Parser + Config-Driven Port

**Phase**: 0 - Technical Research | **Date**: 2026-07-05 | **Spec**: `specs/013-langgraph-workflow/spec.md`

> **Status**: this feature is **Partially Superseded By** `010-langgraph-agent` and
> `012-spec-reconciliation` (see the spec header). The decisions below are recorded as-built.
> Where a decision has since been superseded, that is noted inline with the canonical replacement.

---

## Purpose

Records the Phase 0 research behind the LangGraph workflow, the dual-format Action parser, and the
config-driven Streamlit port. Grounded in `spec.md` (FR-001..012), `plan.md` (Architecture, Parser
Dual-Format), `tasks.md` T001-T016, and the canonical decisions in `012` sections 4-5 (ADR-13/15/16).

---

## Current State Analysis

Before this feature the agent used a legacy LangChain `AgentExecutor`. The goal was a modern
LangGraph workflow that works with both tool-calling models (Llama 3.1) and non-tool-calling models
(WhiteRabbitNeo), plus a configurable Streamlit port to avoid conflicts (`spec.md` Input, US3).

---

## Decision 1: Routing by model tool-calling capability

| Option | Pros | Cons |
|--------|------|------|
| A. Auto-detect `tool_calls` support; route to `create_react_agent` (prebuilt) or a custom text-ReAct `StateGraph` | Works with any installed Ollama model | Two code paths to maintain |
| B. Assume tool-calling only | Simpler | Fails on WhiteRabbitNeo (non-tool-calling) |

**Decision**: Option A - `build_workflow()` probes `_supports_tool_calls(llm)` and selects
`_build_prebuilt_workflow` or `_build_custom_workflow`.
*Traceability*: `spec.md` FR-001..003, US1; `plan.md` Architecture; `tasks.md` T003.
*Superseded scope*: as the top-level agent topology, this is superseded by `010`'s explicit node
graph (`012` section 4, ADR-15); the **capability probe itself is retained** and migrates into
`app/core/agent/`.

---

## Decision 2: Action parsing format

| Option | Pros | Cons |
|--------|------|------|
| A. Dual-format regex parser: JSON `Action: {"name": "tool", "input": "value"}` first, text ReAct fallback | Accepts JSON-tuned and classic ReAct models | Regex brittleness |
| B. Text ReAct only | Simple | Rejects JSON-structured models |

**Decision (as-built)**: Option A, accepting JSON keys `name|action|tool` and `input|arguments|arg`,
falling back to text, and returning a format error for one retry on unrecognized output.
*Traceability*: `spec.md` FR-004..009, US2; `plan.md` Parser Dual-Format; `tasks.md` T006-T009.
*Superseded scope*: `012` section 5 / ADR-13 make **structured decoding (Ollama `format=json` /
native `tool_calls`) the primary path**, with this dual-format regex parser retained only as the
fallback.

---

## Decision 3: Config-driven Streamlit port

| Option | Pros | Cons |
|--------|------|------|
| A. `scripts/get_port.py` reads `streamlit.port` from `config.yaml`; launchers call it | One place to change the port | A tiny extra script |
| B. Hardcode the port in each launcher | No script | Port drift across launchers |

**Decision**: Option A. `get_port.py` prints the configured port; all launchers set it dynamically.
*Traceability*: `spec.md` FR-010..011, US3, NFR-004; `plan.md` Config-Driven Port; `tasks.md`
T012-T016.
*Canonical value*: the port is **12199** and `get_port.py`'s fail-safe default equals it
(`012` section 2.6, ADR-16). The as-built `8199`/`8501` values are superseded.

---

## Decision 4: Loop bounding and graceful failure

**Decision**: the custom mode caps iterations at `max_iterations` from state; unknown tools, empty
responses, and malformed JSON are handled with error messages rather than crashes.
*Traceability*: `spec.md` FR-005, FR-008, NFR-002..003; `tasks.md` T020-T026.

---

## Alternatives rejected

- **Keep the legacy `AgentExecutor`** - rejected; it could not cleanly support non-tool-calling
  models or cyclic feedback (`spec.md` Input; architecture ADR-12).

---

## Decision Traceability Summary

| Decision | Spec ref | Tasks | Canonical status |
|----------|----------|-------|------------------|
| 1 Capability routing | FR-001..003 | T003 | probe retained; topology superseded by 010 (ADR-15) |
| 2 Dual-format parser | FR-004..009 | T006-T009 | retained as fallback behind format=json (ADR-13) |
| 3 Config-driven port | FR-010..011 | T012-T016 | canonical port 12199 (ADR-16) |
| 4 Loop bounding | FR-005, FR-008 | T020-T026 | consistent with 010 bounded graph |

---

## Open Questions

None. All decisions are present in `spec.md`/`plan.md`; supersession is governed by
`012-spec-reconciliation`.
