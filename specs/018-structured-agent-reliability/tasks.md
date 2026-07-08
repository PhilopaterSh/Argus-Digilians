# Tasks: Structured-Output Reliability for ArgusBrain

**Feature**: `018-structured-agent-reliability`

- [x] T001 Web research: Ollama structured-outputs reliability, LangChain/LangGraph ReAct
  parsing failure patterns and recommended fixes - `research.md`
- [x] T002 Add `_try_structured_final_answer()` to `app/core/agent/react_workflow.py`
  (mirrors `_try_structured_action`, targets `SecurityReport`)
- [x] T003 Fix `route_after_parse()`'s format-error branch to respect `max_iterations`
  (independent bug found while reusing this module - previously unbounded except by
  LangGraph's default `recursion_limit`)
- [x] T004 Add `LiveFeedCallbackHandler.on_graph_event()` to `app/core/agent/react_callback.py`
- [x] T005 Replace `ArgusBrain`'s non-functional `_get_react_agent`/`_get_simple_chain` dual-path
  with `_run_structured_graph()` + `_finalize_graph_output()`, using
  `react_workflow.build_workflow().stream(stream_mode="values")`; `ask()`'s external contract
  unchanged
- [x] T006 Reproduce the exact live failure with a mock LLM (`_RepeatingMalformedLLM`) and prove
  it now terminates within `max_iterations` with an honest error -
  `tests/test_registry/test_brain_ask.py::test_ask_terminates_within_max_iterations_on_repeated_malformed_output`
- [x] T007 Prove the happy path still works: real structured report + live-feed events -
  `tests/test_registry/test_brain_ask.py::test_ask_streams_live_feed_events_via_on_graph_event`
- [x] T008 Unit tests for `on_graph_event` - `tests/test_registry/test_react_callback.py`
- [x] T009 Unit tests for `_try_structured_final_answer` and the `route_after_parse` bug fix -
  `tests/test_langgraph_workflow.py`
- [x] T010 Verify zero regressions: full existing `tests/test_registry/`,
  `tests/test_langgraph_workflow.py` suites, plus `017`'s tests, all green unmodified (except
  the two tests directly renamed/extended in T006/T007)
- [x] T011 Spec Kit paperwork: this `spec.md`/`research.md`/`plan.md`/`tasks.md`;
  `specs/checklist.md` CHK series; `CHANGELOG.md` entry; `docs/ARCHITECTURE_AUDIT_REPORT.md`
  traceability row

## Explicitly out of scope

- Reintroducing a dual-path/feature-flag between the old and new executor - the old path was
  already non-functional (both branches were identical), nothing to preserve.
- Reducing `app/core/prompts.py`'s prompt length for the (now-unused-by-ArgusBrain) classic
  `agent_factory.py` path - that file remains available/tested for other callers but is out of
  this phase's scope.
- Live Ollama/WSL re-run against the real target - the fix is independently verified via
  reproduced-failure + happy-path tests; a live re-run is a nice-to-have follow-up, not a
  blocker for this phase.
