# Tasks: Partitioned Bounded Memory + Dual-Phase Reflection

**Feature**: `019-shared-memory-reflection-upgrade`

**Status**: Fully implemented and verified 2026-07-10 (T001-T014 all complete).

- [x] T001 Added `ArgusMemory.summarize_for_planning(k=3, max_chars=3000)` as a new, additive
  method — `app/core/memory/memory_service.py`. **Deviation from the original plan**:
  `get_blackboard_summary()` itself was deliberately left untouched rather than given a `k`
  param, because its exact `{domain: {data_type: summary}}` shape (one survivor per
  domain+data_type, `tool_name` dropped) is asserted verbatim by existing tests
  (`test_add_finding_multiple_types` et al.) and consumed by `Query_Memory`/TDA/GUI callers with
  no parsing beyond passing the string through - changing its dedup semantics risked a real
  regression for no benefit `summarize_for_planning()` doesn't already provide. Also found, while
  implementing: the real schema's only per-writer signal is `findings.tool_name`, not
  `data_type` as the spec assumed - `summarize_for_planning()` groups by `(domain, tool_name)`,
  the correct analog to SRMM's per-execution-agent partition.
- [x] T002 Unit tests for per-source bounding (3 sources x 5 findings each -> exactly last-3
  per source, verified by exact index, not just count) — `tests/test_memory.py`. Also added a
  `f.id DESC` tiebreaker to the underlying query (rows can share a microsecond timestamp under
  a tight test loop) so "most recent" is deterministic even on ties - a real correctness fix
  surfaced by writing the test, not just a test-flakiness workaround.
- [x] T003 Added `reflection_notes: list[str]` to `ArgusAgentState` —
  `app/core/agent/react_state.py`
- [x] T004 `_build_reflection_note()` implemented and wired into the duplicate-call block —
  `app/core/agent/react_workflow.py`
- [x] T005 `_inter_reflect()` (3x majority vote) implemented, scoped to `EXPLOITATION_TOOLS`
  (`Advanced_Evasion_Probe`, `Secret_Scanner`, `Run_Nikto`, `Run_FFUF`) —
  `app/core/agent/react_workflow.py`
- [x] T006 `_check_early_termination()` implemented, wired into `execute_node` as an
  observation-stream nudge (not a forced structural exit - `_finalize_graph_output()`'s
  "Final Answer:" requirement remains the single source of truth for completion, per
  Constitution VIII) — `app/core/agent/react_workflow.py`
- [x] T007 **Implemented differently than planned**: rather than threading a `cb` parameter into
  `react_workflow.py`'s node functions (which don't currently receive callbacks at all -
  confirmed by reading `brain.py`'s actual `_emit_graph_step()` mechanism before implementing),
  reflection notes are appended as ordinary `"Reflection:"`-prefixed `HumanMessage`s, which
  already flow through `_run_structured_graph()`'s existing per-message loop.
  `_emit_graph_step()` gained one new branch tagging these with status `"reflecting"` instead of
  the generic `"running"` — `app/core/agent/brain.py`. Achieves FR-008's observability goal
  without inventing new callback plumbing.
- [x] T008 `enable_inter_reflection` config flag (default `true`) added and threaded from
  `ArgusConfig` through `brain.py::_run_structured_graph()` into
  `_build_custom_workflow(..., enable_inter_reflection=...)` — `config.yaml`, `app/core/config.py`
- [x] T009 Reflection-note-accumulation test written as
  `test_duplicate_call_reflection_note_is_response_aware` (response-aware note content verified,
  not the full 20-30-attempt XSS-filter scenario the spec's SC-001 originally envisioned - that
  scale of scenario is deferred to `025`'s benchmark suite once it exists) —
  `tests/test_langgraph_workflow.py`
- [x] T010 SC-002 majority-vote splits: `test_inter_reflection_majority_success_appends_note`
  (2 yes/1 no) and `test_inter_reflection_majority_inconclusive_appends_note` (2 no/1 yes), plus
  unit-level `test_inter_reflect_majority_yes`/`_no`/`_returns_none_when_all_calls_fail` —
  `tests/test_langgraph_workflow.py`
- [x] T011 `test_inter_reflection_disabled_skips_majority_vote` confirms zero vote calls when
  `enable_inter_reflection=False` — `tests/test_langgraph_workflow.py`
- [x] T012 Full regression run: `tests/test_memory.py` + `tests/test_langgraph_workflow.py` +
  `tests/test_registry/` = 91 passed, 0 failed. Full repo suite (`tests/`, excluding
  `ai_benchmark.py`'s standalone script) = 239 passed, 1 failed
  (`test_smart_web_search.py::test_attempt_limit`) - confirmed via `git stash` (re-running the
  identical test with today's changes fully reverted still fails identically) that this failure
  is **pre-existing and unrelated** to this phase: it depends on a live DuckDuckGo network call
  and asserts a `_max_attempts` attribute `SmartWebSearch` does not currently have, in a file
  this phase never touched.
- [x] T013 Measured against the real production model
  (`hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M`, live Ollama, confirmed
  reachable). **Deliberately did not run a full end-to-end scan comparison** (on vs. off) -
  variable tool/network latency would dominate and confound the measurement of what the flag
  itself costs. Instead isolated the exact added operation: 3 interleaved rounds, post-warm-up,
  alternating one normal ReAct action-generation call vs. one full `_inter_reflect()` call (3x
  vote) against the identical live model/prompt shape. Results: single call avg **10.96s**
  (10.28/13.80/8.79s); `_inter_reflect()` avg **0.82s** (0.80/0.84/0.83s, notably *consistent*
  across rounds unlike the single-call times, which vary with output length). Overhead is
  **negative** relative to a naive "3x" expectation - the vote prompt constrains output to one
  word, and decode time is output-token-bound, not input-size or round-trip-count bound.
  **Conclusion: `enable_inter_reflection=true` confirmed safe as the default** - the real
  measured cost is the opposite of NFR-002's original worry. Scripts:
  `measure_inter_reflection_cost.py`/`_v2.py` (scratchpad, not committed - the numbers are
  recorded here and in CHANGELOG.md/checklist.md CHK099 instead).
- [x] T014 `CHANGELOG.md` entries (implementation pass + this verification pass) +
  `specs/checklist.md` new "Phase 019" section (CHK091-100) + Backlog table status update +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row updated to "Implemented"

## Explicitly out of scope (see spec.md)

- Multi-agent split (`020-multi-agent-role-separation`)
- DAG-based path planning (depends on 020)
- Formal proof of SRMM's five properties
