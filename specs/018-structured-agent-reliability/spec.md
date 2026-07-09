# Feature Specification: Structured-Output Reliability for ArgusBrain's ReAct Loop

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `018-structured-agent-reliability`

**Created**: 2026-07-08

**Status**: Implemented

**Input**: Live production failure, first real end-to-end run of `017-restore-react-agent`: a
scan against `https://www.cultbeauty.co.uk/` timed out after 900s with zero results. User asked
for the best available fix, researched properly, and formalized as a Spec Kit phase.

---

## Why this feature (incident summary)

Real run log (`logs/agent_runs/agent_9a5671bc-....json`): WhiteRabbitNeo-V3-7B, given a large
fused context (`[BRAIN] Fusion context: RAG + Blackboard (6123 chars)`), never once produced a
valid `Thought:/Action:/Action Input:` line across ~26 retries over 15 minutes - it repeated the
identical malformed dump of raw context data every time, each rejected by LangChain
(`"Invalid Format: Missing 'Action:' after 'Thought:'"`), until the wall-clock timeout killed
the run with `Overall Risk Score: N/A`, `Findings Count: 0`.

`ArgusBrain`'s own docstring already claimed a defense: *"When WhiteRabbitNeo has format issues
with ReAct, automatically falls back to a simpler sequential execution model."* Code inspection
found this was never true - `_get_react_agent()` and `_get_simple_chain()` both called the
identical `app/core/agent/agent_factory.py::build_agent_executor()` (classic LangChain
`create_react_agent` + `AgentExecutor`, pure free-text parsing), differing only in
`verbose=True` vs `False`. No actual fallback existed.

A second, independent bug was found while fixing the first: `app/core/agent/react_workflow.py`'s
`route_after_parse()` routed a "format_error" phase straight back to the `agent` node with **no
`max_iterations` check at all** (unlike the tool-execution path, which does check it) - so even
switching to this graph without fixing the routing would have left the exact failure mode
unbounded except by LangGraph's default `recursion_limit` (25), surfacing as an ungraceful
`GraphRecursionError` instead of a clean result.

## Research

Web research (2026-07-08) confirms the standard fix for unreliable free-text LLM output:
constrain generation at the sampling level via a JSON schema, rather than parsing free text
after the fact.
- Ollama's own structured-outputs documentation: passing a JSON schema to the `format` field
  (supported since Ollama 0.3.0) "eliminates parsing problems at the root... no code fences, no
  explanatory text... near-100% parse success," roughly 6x more reliable than hoping the model
  follows a text format.
- LangGraph's documented structured-output/fallback patterns: extract with a Pydantic schema,
  validate, and feed errors back through a conditional edge loop; use `.with_fallbacks()` or a
  backup node so a still-failing model returns a clear, honest error instead of crashing or
  silently succeeding with bad data.
- Flatter, shorter system prompts are also a documented reliability lever for smaller local
  models - `app/core/agent/react_prompts.py`'s prompt is already far shorter than
  `app/core/prompts.py`'s 9-phase template.

Full detail: `research.md`.

**The recommended fix already existed in this repository, fully built and tested, just
disconnected from production** (same situation as `017`): `react_workflow.py::_try_structured_action()`
uses exactly this technique (`llm.with_structured_output(_ArgusAction)`), with regex text
parsing only as a fallback - built for the `013-langgraph-workflow` phase specifically to handle
"WhiteRabbitNeo has format issues," per its own comments.

## Requirements

### Functional Requirements

- **FR-001**: `ArgusBrain` MUST route tool selection through `react_workflow.py`'s custom graph
  (structured-output-first, text-fallback-second) instead of `agent_factory.py`'s classic
  `AgentExecutor` (free-text-only, no structural fallback).
- **FR-002**: The final answer MUST also go through structured extraction
  (`_try_structured_final_answer()`, new) targeting `app.core.schemas.SecurityReport` - the same
  reliability fix applied to the report shape, not just tool selection.
- **FR-003**: `ArgusBrain.ask(query, callbacks=None)`'s external contract MUST NOT change -
  `scripts/run_agent.py`, `app/core/agent/brain_tools.py`, and `app/GUI/tabs/agent.py` (all
  `017` code) require zero changes.
- **FR-004**: Live-feed streaming MUST continue to work without GUI changes - `LiveFeedCallbackHandler`
  gains a new `on_graph_event(status, detail)` method, called directly from `ArgusBrain`'s new
  streaming loop (a raw `StateGraph` doesn't fire `AgentExecutor`'s callback hooks).
- **FR-005**: `route_after_parse()`'s format-error retry path MUST respect `max_iterations`,
  closing the independent bug found above.
- **FR-006**: A run that never reaches a valid Final Answer MUST report an honest
  `no_final_answer`/`graph_execution_failed` error - MUST NOT fabricate a report (Constitution
  VIII - Truthful Runtime), and MUST terminate within `max_iterations`, not run until an outer
  timeout.

### Non-Functional Requirements

- **NFR-001**: `max_iterations` for the structured graph is **15** (not the old
  `AgentExecutor`'s 50) - structured decoding needs far fewer retries, and it bounds worst-case
  wall-clock time better given each iteration can be a slow real tool call.
- **NFR-002**: Fully unit-testable without live Ollama/WSL, matching the existing
  `tests/test_registry/test_brain*.py` and `tests/test_langgraph_workflow.py` fake/mock-LLM
  patterns.

## Success Criteria

- **SC-001**: A mock LLM that reproduces the exact live failure (repeats identical non-ReAct
  output every call) causes `ArgusBrain.ask()` to terminate within `max_iterations` with an
  honest error - verified directly, not just asserted.
- **SC-002**: A well-behaved mock LLM still produces a real structured `SecurityReport` and
  streams live-feed events correctly - the fix does not regress the happy path.
- **SC-003**: All existing `tests/test_registry/`, `tests/test_langgraph_workflow.py`, and
  `017` tests stay green.

## Assumptions

- A live Ollama/WSL re-run against the same real target is the strongest possible confirmation
  but is not required to land this fix - the failure and the fix are both independently
  verified with injected fake/mock LLMs, following this repo's established testing convention.

## Addendum: live re-run findings (2026-07-09)

The live re-run in the Assumptions section above was in fact performed, against the same real
target. It found four additional real bugs the mock-LLM suite couldn't reach, plus one
infrastructure-level crash outside this codebase's control. Full detail in `research.md`'s
addendum and `CHANGELOG.md`; tracked as CHK077-082 in `specs/checklist.md`.

- **FR-007**: `ArgusBrain`'s LLM MUST be chat-style (`ChatOllama`) when `with_structured_output`
  is required - `OllamaLLM` (completion-style) raises `NotImplementedError`, confirmed live.
  `llm_factory.py::build_chat_llm()` added; `build_llm()` unchanged for its other callers.
- **FR-008**: `get_blackboard_summary()` MUST bound its output by default (`max_chars=3000`) -
  unbounded growth across every target ever scanned fed an oversized prompt into a live run and
  contributed to a GPU crash. An explicit larger `max_chars` MUST still return everything.
- **FR-009**: `ArgusBrain` MUST route to `react_workflow.py`'s custom graph explicitly
  (`_build_custom_workflow()`), not through `build_workflow()`'s tool-support auto-detection -
  `ChatOllama.bind_tools()` succeeding (unlike `OllamaLLM`'s) was confirmed live to silently
  select the untested prebuilt graph, whose state shape `ArgusBrain`'s output parsing doesn't
  match.
- **FR-010**: The agent's `target` MUST be extracted from the raw, pre-RAG-enrichment query, not
  the enriched one - `_enrich_with_rag()` prepends a Blackboard JSON block that
  `extract_target()`'s heuristic can mistake for the target, confirmed live to break every tool
  call with a corrupted target string.
- **FR-011**: A specific, known transient Ollama/CUDA crash signature
  (`"llama-server process has terminated"` / `"CUDA error"`) MUST trigger exactly one retry
  (fresh graph + fresh model load) before failing; any other exception MUST fail immediately
  without a retry (Constitution VIII - never mask an unrelated failure behind a retry). This is
  a mitigation, not a fix - the underlying driver/Ollama bug (matches upstream
  `ollama/ollama` issue #16650) is out of scope for an application-level fix.

### Success Criteria (addendum)

- **SC-004**: `test_ask_extracts_target_before_blackboard_enrichment_not_after` proves the real
  target reaches tool calls even when the Blackboard summary contains a JSON key shaped like a
  dot-separated hostname.
- **SC-005**: `test_ask_retries_once_on_transient_ollama_cuda_crash` and
  `test_ask_does_not_retry_non_infra_errors` prove the retry is scoped to the exact known
  failure signature, not a general safety net.
