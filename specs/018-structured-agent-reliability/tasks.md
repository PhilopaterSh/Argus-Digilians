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

## Addendum: live re-run tasks (2026-07-09)

The live re-run above was performed and found four more real bugs plus one infra-level crash -
see `spec.md`'s addendum (FR-007-011) and `research.md`'s addendum for full detail.

- [x] T012 `app/core/llm_factory.py`: add `build_chat_llm()` (returns `ChatOllama`); `build_llm()`
  left unchanged for `reflective_node`/`rag_engine.py`
- [x] T013 `app/core/memory/memory_service.py`: bound `get_blackboard_summary(max_chars=3000)`
  by default, priority/recency-ordered, never mid-entry-truncated; explicit larger `max_chars`
  still returns everything
- [x] T014 `app/core/agent/brain.py`: call `react_workflow._build_custom_workflow()` directly
  instead of `build_workflow()`'s tool-support auto-detection (which `ChatOllama.bind_tools()`
  succeeding would otherwise silently route to the untested prebuilt graph)
- [x] T015 `app/core/agent/brain.py::ask()`: extract `target` from the raw pre-enrichment query,
  pass explicitly into `_run_structured_graph(query, target, callbacks)` - fixes
  `extract_target()` reading a corrupted target out of the RAG-enriched query
- [x] T016 `app/core/agent/brain.py::_run_structured_graph()`: one-time retry keyed on the exact
  transient Ollama/CUDA crash signature (`_TRANSIENT_INFRA_ERROR_MARKERS`,
  `_MAX_INFRA_RETRIES = 1`); any other exception fails immediately, no retry
- [x] T017 `scripts/LAUNCH_STUDIO.bat`: `OLLAMA_KV_CACHE_TYPE=q8_0` + `OLLAMA_FLASH_ATTENTION=1`
  to reduce VRAM pressure (one contributing factor to T016's crash)
- [x] T018 Regression tests: `test_ask_extracts_target_before_blackboard_enrichment_not_after`,
  `test_ask_retries_once_on_transient_ollama_cuda_crash`,
  `test_ask_does_not_retry_non_infra_errors`,
  `test_memory.py::test_large_insert_performance` updated for bounded-by-default behavior
- [x] T019 Verify zero regressions: full suite green (186 passed, 1 pre-existing unrelated
  network-dependent failure)
- [x] T020 Spec Kit paperwork for the addendum: this `tasks.md`/`spec.md`/`research.md`;
  `specs/checklist.md` CHK077-082; `CHANGELOG.md` entry
- [ ] T021 Model/quantization switch (user-confirmed direction, 2026-07-09): pull
  `hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M` via Ollama, update
  `config.yaml`'s `model_name` (and `scripts/ARGUS_INSTALLER.ps1`'s default `$OLLAMA_MODEL` for
  fresh installs), verify live that the quantized model still produces valid structured output
  and tool calls before treating this as done
