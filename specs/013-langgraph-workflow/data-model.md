# Data Model: LangGraph Workflow + JSON Parser + Config-Driven Port

**Phase**: 1 - Design | **Date**: 2026-07-05 | **Spec**: `specs/013-langgraph-workflow/spec.md`

> **Status**: Partially Superseded By `010-langgraph-agent` + `012-spec-reconciliation`. Canonical
> agent state is `AgentState` in `app/core/agent/state.py` (`012` data-model Entity 2); the state
> objects below are the as-built `app/core/workflow/` structures, retained until the migration in
> `012` T028.

---

## Purpose

Documents the in-memory structures of the as-built workflow: the two agent state schemas, the parser
output, and the config-driven port. The workflow is stateless on disk (state is held in-memory by
LangGraph; `plan.md` Technical Context: "Storage: None"). Derived from `spec.md` Key Entities and
`plan.md` Architecture / Parser Dual-Format.

---

## Entity 1: ArgusAgentState (custom mode)

TypedDict state for the custom text-ReAct `StateGraph` (`app/core/workflow/state.py`).

| Field (derived from spec/plan) | Purpose |
|--------------------------------|---------|
| messages / scratchpad | Thought -> Action -> Observation history |
| current tool + input | Parsed Action to execute |
| iteration count | Loop counter |
| max_iterations | Iteration cap (spec FR-005) |
| phase | `continue` / `done` / `tool_error` (from parser) |

**Invariant**: the graph ends when phase is `done` (Final Answer) or `iteration == max_iterations`
(`spec.md` FR-003, FR-005).

---

## Entity 2: ArgusPrebuiltState (prebuilt mode)

State for `create_react_agent` (prebuilt mode), which uses `remaining_steps` for the automatic loop
cap (`spec.md` FR-002; `plan.md` Architecture).

| Field | Purpose |
|-------|---------|
| messages | LangGraph message channel |
| remaining_steps | Automatic loop cap for prebuilt agents |

---

## Entity 3: ParsedAction (parser output)

Produced by `_parse_react_output(content, default_input)` (`plan.md` Parser Dual-Format).

| Field | Type | Source keys (JSON mode) |
|-------|------|-------------------------|
| phase | enum(`continue`,`done`,`tool_error`) | detected from content |
| tool_name | str | `name` \| `action` \| `tool` (spec FR-006) |
| tool_input | str | `input` \| `arguments` \| `arg` (spec FR-007) |

**Invariant**: malformed JSON falls back to text ReAct, not a crash (`spec.md` FR-008); unrecognized
format returns a `tool_error` for one retry (`spec.md` FR-009).
*Canonical note*: per `012` section 5 / ADR-13, structured decoding (`format=json` / native
`tool_calls`) is the primary producer of this structure; the regex parser is the fallback.

---

## Entity 4: PortConfig

| Field | Type | Source |
|-------|------|--------|
| streamlit.port | int | `config.yaml` -> read by `scripts/get_port.py` |
| fail-safe default | int | printed if `config.yaml` is missing/unreadable |

**Invariant**: canonical value **12199**; the fail-safe default equals the configured value so no
drift is possible (`012` section 2.6, ADR-16; `spec.md` NFR-004 as refined).

---

## Relationships

```text
build_workflow(llm, tools)
  |-- supports_tool_calls -> ArgusPrebuiltState (create_react_agent)
  |-- not supported       -> ArgusAgentState (custom StateGraph)
                                 parse_node -> ParsedAction -> execute_node -> agent (loop)
get_port.py --reads--> PortConfig(config.yaml) --> launchers
```

---

## Acceptance Criteria (data model)

- **AC-1**: A tool-calling model routes to prebuilt mode; a non-tool-calling model routes to custom
  mode (`spec.md` FR-001, US1 AC-1/AC-2).
- **AC-2**: `ParsedAction` extracts tool_name/tool_input from all accepted JSON key variants and from
  text ReAct (`spec.md` FR-006..007, US2).
- **AC-3**: Malformed JSON never crashes the parser (`spec.md` FR-008).
- **AC-4**: Changing `streamlit.port` in `config.yaml` propagates to all launchers (`spec.md` SC-004);
  canonical value 12199 (ADR-16).

---

## Implementation Notes

- Exact field names live in `app/core/workflow/state.py`; this document is the conceptual model.
- Under the `012` reconciliation, these structures migrate into `app/core/agent/` and the parser
  becomes the fallback path (`012` T028, T030). This file is retained for the as-built record.
