# Implementation Plan: Partitioned Bounded Memory + Dual-Phase Reflection

**Feature**: `019-shared-memory-reflection-upgrade` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

Two independent-but-complementary upgrades inside files Argus already owns: (1)
`ArgusMemory.get_blackboard_summary()` gains per-source bounded aggregation; (2)
`react_workflow.py`'s duplicate-call block gains a structured reflection payload, and a new
3x-majority-vote Inter-reflection check gates whether an exploitation-style tool result counts
as a confirmed success. No new files' worth of new subsystem — this is a modification of
`memory_service.py`, `react_workflow.py`, and `react_state.py`.

## Design

### `app/core/memory/memory_service.py`
- `add_finding()` unchanged — already carries `source`.
- New `get_blackboard_summary(max_chars=3000, k=3)`: query groups findings by `source`, take the
  most recent `k` per group (ordered by existing recency/priority logic), format each as
  `[source] title: detail`, join groups in existing priority order, then apply `max_chars`
  truncation only if the k-bounded result still exceeds it (should be rare — `k * num_sources *
  ~80 chars/entry` for Argus's current ~10 sources and k=3 is well under 3000).
  Existing callers (`ArgusBrain._refresh_blackboard()`) get the new default (`k=3`) with no
  call-site change; a larger explicit `k` still returns more, matching `018`'s existing
  "explicit larger max_chars still returns everything" precedent (FR-002 in spec.md).
- New `summarize_for_planning(k=3)`: thin wrapper calling the above with the `[source] ...`
  formatting made explicit in its own docstring (FR-004) — kept as a separate, named method
  (rather than folding into `get_blackboard_summary`) so a future 020 multi-agent split can
  redirect *only* the planner-reading call site to this method without touching the
  general-purpose summary callers.

### `app/core/agent/react_state.py`
- `ArgusAgentState` gains `reflection_notes: list[str]` (new field, default `[]`) — holds the
  structured "action X failed because Y, try changing Z" strings the new Intra-reflection step
  produces, separate from raw `tool_call_history` so the prompt-building code in
  `react_workflow.py` can render them distinctly.

### `app/core/agent/react_workflow.py`
- The existing "3rd identical call" branch changes from appending a generic string to calling
  new `_build_reflection_note(prior_action, prior_response) -> str` — extracts the HTTP
  status/error substring already present in most tool outputs (reuses existing
  `command_runner.py` output shapes, no new parsing library) and one concrete suggested change
  ("try a different encoding," "try a different HTTP method") selected by simple keyword
  matching on the response text (e.g., "403"/"blocked" → suggest encoding change; "timeout" →
  suggest a different endpoint/method) — a lightweight heuristic, not a second LLM call, to
  avoid adding latency to every retry.
- New `_inter_reflect(llm, action, response) -> bool` implementing FR-006: three fixed-prompt
  `llm.invoke()` calls ("did the following tool call achieve its goal? answer yes or no only"),
  majority vote. Called only for tool names in a small `EXPLOITATION_TOOLS` allowlist constant
  (`Advanced_Evasion_Probe`, `Secret_Scanner`, `Run_Nikto`, `Run_FFUF` initially — the tools
  whose raw output requires interpretation) defined at module level, imported by
  `brain_tools.py`'s tool-name constants rather than duplicated (Constitution IX).
- New `_check_early_termination(text, pattern=r"flag\{[^}]+\}") -> bool` (FR-007), called
  alongside the existing `Final Answer:` check in the same routing function.
- Each new call emits `cb.on_graph_event("reflecting", detail)` before returning, per FR-008.
- `enable_inter_reflection` read from `ArgusConfig` (new field, default `True`) at graph-build
  time; when `False`, `_inter_reflect` is skipped and the raw tool result is trusted as before
  (018's current behavior) — satisfies NFR-002's escape hatch.

### `config.yaml` / `app/core/config.py`
- New `enable_inter_reflection: true` under the existing agent-config section, following the
  same pattern as other existing boolean feature flags in that file.

## Testing Strategy

Mock-LLM-only, matching `018`'s established pattern (`FakeListLLM`/custom mock classes in
`tests/test_registry/test_brain_ask.py`, `tests/test_langgraph_workflow.py`). Three new test
groups: (1) per-source bounded aggregation on `ArgusMemory` directly (no LLM needed — pure data
logic, `tests/test_memory.py`); (2) the SC-001 filtered-XSS-style scenario with a mock tool
returning progressively different "stripped" responses, asserting reflection notes accumulate
and get surfaced in the next prompt; (3) the SC-002 majority-vote scenarios (2-1 and 1-2 splits)
with a mock LLM whose `invoke()` is configured to return an exact sequence of yes/no strings.

## Rollout

`enable_inter_reflection: true` by default per NFR-002, but with the config escape hatch —
unlike `018`'s "no dual-path" stance (justified there because the old path was already
non-functional), here the underlying single-LLM-pass behavior is currently working, so a
feature flag is warranted until real wall-clock impact under `max_iterations=15` is measured
against a live target, not just mocked.
