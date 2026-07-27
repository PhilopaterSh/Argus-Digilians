# Implementation Plan: Human-in-the-Loop Escalation on Detected Stuck Loops

**Feature**: `028-human-in-the-loop-escalation` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

A new, structural "stuck" detector inside `execute_node` (single-loop graph) that calls
LangGraph's native `interrupt()`, a new GUI status/input surface for resolving it, and a
non-negotiable timeout-based auto-resume so unattended (CLI/headless) runs are completely
unaffected. Behind `enable_hitl_escalation` (default `false`).

## Design

### `app/core/agent/react_workflow.py`
- New module-level helper `_detect_stuck_pattern(reflection_notes: list[str], iteration_count:
  int, max_iterations: int, blackboard_findings_this_run: int, stuck_reflection_count: int,
  stuck_iteration_fraction: float) -> Optional[str]` (pure function, testable without a graph -
  matches `_check_early_termination`/`_extract_vulnerability_hints`'s existing style): returns a
  human-readable reason string if either FR-001 condition holds, else `None`.
- `execute_node` (or its `_run_specialist_step` sibling in `020`'s multi-role graph, if ever
  promoted): after appending this call's reflection notes, call `_detect_stuck_pattern()`. If it
  returns a reason and `enable_hitl_escalation` is true, call `interrupt({"reason": ...,
  "blackboard_summary": state["blackboard_summary"], "recent_reflection_notes": ...})` (FR-002)
  instead of returning normally. The value `interrupt()` returns on resume (a human hint string,
  or `""` on FR-005's timeout) is appended to `reflection_notes` via the exact same
  `_build_reflection_note`-populated-field mechanism already in use - no new state shape.
- Graph compilation (`_build_custom_workflow`) must pass a checkpointer to `StateGraph.compile()`
  (`checkpointer=MemorySaver()` for a single-process run, per NFR-003 - verify LangGraph's
  current API for this against the actually-installed version before assuming the exact call
  shape matches older documentation).

### `app/core/agent/brain.py`
- `_run_structured_graph`'s `graph.stream(...)` loop: an `interrupt()` surfaces as a special
  entry in the stream (LangGraph's own convention - verify exact shape at implementation time,
  T001). On seeing it, call a new `cb.on_needs_input(payload)` (mirrors `on_graph_event`'s
  existing thin-wrapper pattern in `react_callback.py`) instead of `_emit_graph_step`, then
  **block on a bounded wait** (FR-005's timeout, read from
  `ArgusConfig.load().hitl_escalation.timeout_seconds`) for a resume value written to the run's
  state file (see `app/GUI/tabs/agent.py` below) before calling
  `graph.invoke(Command(resume=resume_value), config)` to continue. If the timeout elapses with
  no value written, resume with `""` (auto-continue, FR-005) - this wait happens in the
  subprocess `scripts/run_agent.py` spawns for GUI-driven runs; a direct CLI invocation
  (`scripts/run_argus_cli.py`) has no GUI writing a resume value, so it always hits the timeout
  and auto-continues, satisfying SC-004 by construction, not by a separate code path.

### `app/GUI/tabs/agent.py` / `AgentController`
- New status value `"needs_input"` in the run state file's `status` field (FR-003) - additive to
  the existing `"running"`/`"reflecting"`/`"completed"`/`"failed"` vocabulary the dashboard
  already renders, not a parallel system.
- New small render block: when `status == "needs_input"`, show the interrupt payload (reason +
  Blackboard summary + recent reflection notes) and a text input + "Send hint" button. Submitting
  writes the hint into the run's state file (a new `pending_resume` field) for `brain.py`'s
  blocked wait (above) to pick up - reuses the existing state-file-as-IPC mechanism `018`/`019`
  already established between the GUI process and the agent subprocess, not a new channel.

### `config.yaml` / `app/core/config.py`
- New `HITLEscalationSettings` dataclass (matching `RAGSettings`/`StreamlitSettings`'s existing
  pattern): `enabled: bool = False`, `stuck_reflection_count: int = 3`,
  `stuck_iteration_fraction: float = 0.8`, `timeout_seconds: int = 300` (NFR-001).

## Testing Strategy

Same mock-LLM convention as `019`/`020`. `_detect_stuck_pattern()` gets direct unit tests (pure
function, no graph needed) for both trigger conditions and the "not stuck" negative case.
`interrupt()`/`Command(resume=...)` integration tested via LangGraph's own testing utilities for
this exact pattern (verify what those are for the installed version at T001 - do not assume
without checking, matching this project's established "verify before implementing" discipline).
SC-004 (CLI runs unaffected) is the most safety-critical test in this spec and must be run
against a real `scripts/run_argus_cli.py` invocation, not just a mocked graph, before this
feature is ever considered for anything beyond `enable_hitl_escalation: false`.

## Rollout

Feature-flagged (`enable_hitl_escalation: false` by default), same stance as `020` - a genuinely
new, unmeasured behavior, not a proven mechanism being generalized. Promote to default only
after: (a) SC-004 confirms zero behavior change for unattended runs, (b) live GUI-monitored runs
confirm the "needs_input" surface actually helps (subjective, requires the user's own judgment
watching it happen at least once), and (c) FR-005's timeout path is confirmed to never misfire
during normal operation (i.e. it doesn't trigger on runs that are legitimately still making
progress, just slowly).
