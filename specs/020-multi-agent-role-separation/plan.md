# Implementation Plan: Multi-Agent Role Separation

**Feature**: `020-multi-agent-role-separation` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

**Not recommended to start until `019` ships and its residual gap is measured.** This plan is
written so the option is concretely scoped, not left vague — if approved, it is a graph-topology
change inside `react_workflow.py`, not a rewrite of `ArgusBrain` or the tool layer.

## Design (if approved)

### `app/core/agent/react_prompts.py`
- Split the single system prompt into 4 role prompts: `PLANNER_PROMPT`, `COLLECTOR_PROMPT`,
  `EXPLOITER_PROMPT`, `SUMMARIZER_PROMPT` — each a trimmed-down variant of the current prompt
  scoped to that role's responsibility and tool subset, keeping the same flat, non-9-phase
  style `018` found more reliable for this model than `app/core/prompts.py`'s original template.

### `app/core/agent/brain_tools.py`
- New `build_argus_tools(bridge, role=None)` optional `role` parameter returning the FR-002
  subset when specified; `role=None` (default) keeps returning the full 17-tool list, so `019`
  and any caller not opting into this phase is unaffected — additive, not a breaking signature
  change.

### `app/core/agent/react_workflow.py`
- New graph topology: `planner` node (decides phase + next role to invoke, reads
  `summarize_for_planning()` from `019`, never calls `add_finding`) -> conditional edge to
  `collector` or `exploiter` node (each scoped to FR-002's tool subset, writes findings via
  `add_finding` with its own name as `source`) -> back to `planner` -> ... -> `summarizer` node
  (terminal, builds the `SecurityReport` via `018`'s `_try_structured_final_answer`).
- `route_after_parse()`/`max_iterations` bounding logic is reused unchanged — the iteration
  budget still counts every node visit regardless of role, preventing any one role from looping
  unboundedly.

### `app/core/agent/react_state.py`
- `ArgusAgentState` gains `current_role: str` and `role_history: list[str]` (for post-run
  auditing of how much time was spent in which role — directly useful for NFR-001's wall-clock
  measurement).

## Testing Strategy

Same mock-LLM convention as `019`/`018`. Critically: a **head-to-head wall-clock comparison
test harness** (not just correctness tests) comparing this topology against the `019`-only
single-loop baseline on the same mocked tool-latency profile, to produce the NFR-001 numbers
before any live-target run is attempted.

## Rollout

Feature-flagged (`enable_multi_agent_roles: false` by default in `config.yaml`) rather than a
hard replacement — unlike `018`'s "no dual-path" stance, here the existing single-loop path is
the proven-stable production default and this is a genuinely uncertain-value experiment, the
opposite situation from `018`'s non-functional old path. Only promote to default after SC-001
and SC-002 are both met on real measurements, not projections.
