# Feature Specification: Restore ArgusBrain (Prompt-Driven ReAct Agent) as Production Driver

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `017-restore-react-agent`

**Created**: 2026-07-08

**Status**: Implemented — **Canonical Reconciliation event** (Constitution VII). Supersedes
`010-langgraph-agent`'s deterministic graph as the *production driver* for `app/GUI/dashboard.py`'s
"Start Agent" button. `010`'s graph code is retained in-repo (Constitution VII: superseded
artifacts are not silently deleted) and its own tests remain green; it is simply no longer
invoked from `scripts/run_agent.py`.

**Input**: User-directed investigation: "the idea of the project is that the AI follows
instructions and a predefined path in `app/core/prompts.py`, runs the tool it's directed to,
sees the result, and decides the best next path based on it" - confirmed via code inspection to
be the project's actual original design, already fully implemented but disconnected from
production.

---

## Why this feature (reconciliation rationale)

Direct investigation (this session) found:
- `app/core/prompts.py::ARGUS_AGENT_TEMPLATE` defines a classic ReAct
  (Thought/Action/Observation) prompt with 9 operational phases and a structured JSON final
  answer format.
- `app/core/agent/brain.py::ArgusBrain` already uses this prompt via
  `app/core/agent/agent_factory.py::build_agent_executor()`, which always constructs a real
  LangChain `create_react_agent` + `AgentExecutor` (free tool choice, not a fixed sequence).
- `ArgusBrain(...)` is instantiated **only** by the deprecated GUI shims
  (`app/GUI/{app,argus_gui,gui_main}.py`) and the Tkinter fallback (`desktop_gui.py`) - never by
  the canonical `app/GUI/dashboard.py`, which instead drives
  `scripts/run_agent.py` -> `app/core/agent/graph.py::build_tactical_graph()` (deterministic
  recon -> scanner -> exploit -> reflective, with only one narrow single-token LLM call).

This is exactly the situation Constitution VII exists for: the production system was running a
different design than the one the project's own prompt/brain infrastructure was built for and
still fully supports.

---

## Requirements

### Functional Requirements

- **FR-001**: `scripts/run_agent.py` MUST drive `ArgusBrain.ask()` (free tool-choosing ReAct
  loop) instead of `build_tactical_graph()`.
- **FR-002**: The tool list available to `ArgusBrain` MUST be built from a single canonical
  location (`app/core/agent/brain_tools.py::build_argus_tools()`), not duplicated per caller
  (Constitution IX).
- **FR-003**: Each ReAct step (Thought/Action/Observation, tool errors, final answer) MUST be
  streamed live into the existing state-file event contract
  (`app/core/agent/contracts.py::append_run_event`) via a callback handler
  (`app/core/agent/react_callback.py::LiveFeedCallbackHandler`), so `app/GUI/tabs/agent.py`'s
  "Agent Feed" shows it with zero GUI polling changes.
- **FR-004**: The final persisted result MUST be the real `SecurityReport`-shaped output
  `ArgusBrain.ask()` produces (`summary`, `attack_surface_stats`, `findings`,
  `overall_risk_score`, `next_steps`, `output`) - MUST NOT force it into the old
  `open_ports`/`vulnerabilities`/`exploit_success` shape.
- **FR-005**: If the agent's output isn't a valid structured report, the persisted state MUST
  say so explicitly (`parse_warning`) rather than fabricating empty-looking structured fields
  (Constitution VIII - Truthful Runtime).
- **FR-006**: The existing subprocess timeout-bounding (`threading.Thread(...).join(timeout)`)
  and DEMO/TEST-mode fallback behavior MUST be preserved unchanged.
- **FR-007**: `app/core/agent/graph.py` and its nodes MUST NOT be deleted - retained per
  Constitution VII's superseded-artifact rule, with their existing tests staying green.

### Non-Functional Requirements

- **NFR-001**: No new GUI polling mechanism - reuse the existing state-file/`AgentController`
  contract entirely.
- **NFR-002**: Unit-testable without live Ollama/WSL, matching the existing
  `tests/test_registry/test_brain*.py` pattern (fake-LLM injection via `ArgusBrain(..., llm=)`).

---

## Key Entities

- `app/core/agent/brain_tools.py` - canonical 12-tool list for `ArgusBrain`.
- `app/core/agent/react_callback.py` - `LiveFeedCallbackHandler`, bridges LangChain callbacks to
  the existing state-file event contract.
- `scripts/run_agent.py` - rewritten entrypoint; `_build_final_state()` shapes `ArgusBrain.ask()`'s
  output for persistence.
- `app/GUI/tabs/agent.py` - "Final Results" section updated to render the `SecurityReport` shape.

## Success Criteria

- **SC-001**: Clicking "Start Agent" runs `ArgusBrain`'s ReAct loop; the Agent Feed shows live
  Thought/Action/Observation steps as they happen.
- **SC-002**: A completed run's Final Results show risk score, findings, and the full report -
  not zeroed-out open-ports/vulnerabilities metrics from the old shape.
- **SC-003**: `app/core/agent/graph.py`'s own tests (`tests/test_modules/test_tactical_graph_termination.py`)
  still pass unmodified.
- **SC-004**: Full unit suite green with no live Ollama/WSL required for the new code's own tests.

## Assumptions

- `run_specialized_module` (present in the historical 13-tool list) has no current equivalent on
  `WSLBridgeTools` and is dropped from the 12-tool list - not reintroduced by this feature.
- `AGENT_TIMEOUT_SECONDS` default (900s) is unchanged; a full free-form ReAct run can in
  principle make far more tool calls than the old fixed 3-phase pipeline, so operators running
  long/thorough analyses may need to raise this via the existing env var override.
