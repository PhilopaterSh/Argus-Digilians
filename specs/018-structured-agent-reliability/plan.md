# Implementation Plan: Structured-Output Reliability for ArgusBrain

**Feature**: `018-structured-agent-reliability` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

Reuse `app/core/agent/react_workflow.py`'s custom structured-output-first ReAct graph as
`ArgusBrain`'s internal executor, replacing `app/core/agent/agent_factory.py`'s classic
free-text `AgentExecutor` (which had no real fallback despite `ArgusBrain`'s docstring claiming
one). `ArgusBrain.ask()`'s external contract is unchanged, so `017`'s `scripts/run_agent.py`,
`brain_tools.py`, and `app/GUI/tabs/agent.py` need zero changes.

## Design

### `app/core/agent/react_workflow.py`
- New `_try_structured_final_answer(llm, raw_answer) -> Optional[dict]`: mirrors
  `_try_structured_action`'s pattern, targeting `app.core.schemas.SecurityReport` instead of
  `_ArgusAction`. Applies the same reliability fix to the final report shape.
- Bug fix in `route_after_parse()`: the `format_error` branch now checks
  `iteration_count >= max_iterations` before looping back to `"agent"`, matching the check the
  tool-execution path already had. Without this, the exact incident scenario (model never once
  produces valid output) would loop unbounded except by LangGraph's default `recursion_limit`.

### `app/core/agent/brain.py`
- Removed: `_get_react_agent`, `_get_simple_chain`, `_ask_simple_chain`, `use_react` flag,
  `_react_agent`/`_simple_chain` cached-executor attributes - all dead weight now that there's
  one real path instead of two identical fake ones.
- Added: `DEFAULT_MAX_ITERATIONS = 15` module constant; `self.max_iterations` instance attribute.
- Added: `_run_structured_graph(query, callbacks)` - builds `react_workflow.build_workflow(self.llm,
  self.tools, self.memory)`, streams it via `stream_mode="values"` (yields the full accumulated
  state after each node, simpler to diff than delta-mode), emits one `on_graph_event()` call per
  newly-appended message so callers get live step-by-step visibility without relying on
  `AgentExecutor`'s LangChain-specific callback dispatch (which a raw `StateGraph` never
  triggers).
- Added: `_finalize_graph_output(state)` - extracts the text after `Final Answer:` from the
  last message once `phase == "done"`, tries `_try_structured_final_answer()`, falls further
  back to the existing `_process_output()` (Pydantic/regex-JSON extraction) before finally
  returning the raw text. Returns an honest `{"output": {"error": ..., "message": ...}}` if the
  graph never reached `"done"` - never fabricates a report.
- `ask()` now just does `_refresh_blackboard()` -> `_enrich_with_rag()` -> `_run_structured_graph()`.

### `app/core/agent/react_callback.py`
- New public method `LiveFeedCallbackHandler.on_graph_event(status, detail)` - thin wrapper over
  the existing private `_emit()`. The four existing `AgentExecutor`-hook methods are untouched.

## Testing Strategy

Direct reproduction, not just happy-path coverage - a mock LLM built specifically to replay the
real incident's exact behavior (repeats identical non-ReAct text every call), asserting the
fixed code terminates within `max_iterations` with an honest error instead of hanging/crashing.
Paired with a well-behaved mock proving the happy path (real structured report + live events)
still works. Existing `tests/test_registry/`, `tests/test_langgraph_workflow.py` suites must
stay green untouched, proving `agent_factory.py`/the deterministic `017`-superseded graph
(`app/core/agent/graph.py`, itself already superseded by `017`) are unaffected.

## Rollout

No feature flag / dual-path kept - per this repo's Constitution IX (no duplication) and the
fact that the old dual-path was already non-functional (both branches were identical), there is
nothing to preserve by keeping it. `agent_factory.py::build_agent_executor()` itself is left in
place (still used/tested independently, and by `react_workflow.py`'s prebuilt-mode path for
tool-calling-capable models) - only `ArgusBrain`'s internal wiring changes.
