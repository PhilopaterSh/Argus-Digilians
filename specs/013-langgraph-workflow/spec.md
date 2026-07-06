# Feature Specification: LangGraph Workflow + JSON Parser + Config-Driven Port

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-07-05

**Feature ID**: `013-langgraph-workflow` (renumbered from the duplicate `003` — the original `003` is `003-sqlite-blackboard`, created 2026-06-29).

**Status**: Partially Superseded

**Superseded By**: `010-langgraph-agent` (canonical agent topology) and `012-spec-reconciliation` (canonical decisions).

**Supersession scope**:
- **Superseded** — the generic dual-mode top-level ReAct agent (`_build_prebuilt_workflow` / `_build_custom_workflow`) and its `app/core/workflow/` location. The canonical production agent is the explicit LangGraph node graph in `app/core/agent/` (see `010`).
- **Retained (still canonical)** — the model tool-calling capability probe, the Action parser, the pre/post model hooks, and the config-driven port. Per `012`, these migrate from `app/core/workflow/` into `app/core/agent/` and the parser becomes the *fallback* path behind Ollama `format=json` structured decoding (see `012` ADR-14). The canonical Streamlit port is **12199** (not 8199).

**Input**: Upgrade Argus AI agent from legacy LangChain `AgentExecutor` to a modern LangGraph-based workflow that supports both tool-calling models (Llama 3.1) and non-tool-calling models (WhiteRabbitNeo), with robust JSON/text Action parsing and configurable Streamlit port.

---

## User Scenarios & Testing

### User Story 1 - Hybrid ReAct Agent (Priority: P1)

As a penetration tester, I want the AI agent to work with ANY model I have installed in Ollama, whether it supports tool_calls or not, so I can switch between different models without breaking the analysis pipeline.

**Why this priority**: Core architectural requirement — enables model flexibility.

**Independent Test**: Run `graph_ask()` with Llama 3.1 (tool_calls) and with a non-tool-calling mock. Both should complete a scan → research → report cycle.

**Acceptance Scenarios**:

1. **Given** a model supports `tool_calls` (e.g., Llama 3.1), **When** `build_workflow` runs, **Then** it uses `create_react_agent` (prebuilt mode).
2. **Given** a model does NOT support `tool_calls` (e.g., WhiteRabbitNeo), **When** `build_workflow` runs, **Then** it uses the custom text-based ReAct `StateGraph`.
3. **Given** the custom mode, **When** the LLM outputs a valid Action, **Then** the corresponding tool is executed and the result fed back as an Observation.
4. **Given** the custom mode, **When** the LLM outputs "Final Answer:", **Then** the workflow ends.

---

### User Story 2 - JSON Action Format (Priority: P2)

As a developer integrating new models, I want the parser to accept `Action: {"name": "tool", "input": "value"}` (JSON) in addition to the legacy `Action: tool\nAction Input: value` (text), so models trained on JSON-like structured output can be used directly.

**Why this priority**: Enables compatibility with models fine-tuned for JSON output.

**Independent Test**: Feed the parser `Action: {"name": "mock_scan", "input": "https://test.com"}` and verify it extracts `tool_name=mock_scan`, `tool_input=https://test.com`.

**Acceptance Scenarios**:

1. **Given** the LLM output contains `Action: {"name": "tool", "input": "value"}`, **When** parsed, **Then** the tool name and input are extracted correctly.
2. **Given** alternative JSON keys like `action`, `tool`, `arguments`, `arg`, **When** parsed, **Then** they are accepted as valid.
3. **Given** malformed JSON in the Action line, **When** parsed, **Then** the system falls back gracefully to text ReAct format.
4. **Given** neither JSON nor text format is detected, **When** parsed, **Then** a format error message is returned to the model for retry.

---

### User Story 3 - Config-Driven Port (Priority: P2)

As an operator, I want all launcher scripts to read the Streamlit port from `config.yaml` instead of using hardcoded values, so I can change the port in one place.

**Why this priority**: Prevents port conflict errors when multiple instances run.

**Independent Test**: Change `streamlit.port` in `config.yaml` to a different value, launch the GUI, verify it starts on the new port.

**Acceptance Scenarios**:

1. **Given** `config.yaml` defines `streamlit.port: 12199` (canonical port per `012`), **When** any launcher (`LAUNCH_STUDIO.bat`, `Launch_Argus.bat`, `Run_Argus_Studio.bat`) starts, **Then** Streamlit runs on port 12199.
2. **Given** the port is changed in `config.yaml`, **When** launchers are restarted, **Then** they pick up the new port without code changes.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST auto-detect model tool_calling capability and route to the correct workflow mode.
- **FR-002**: Prebuilt mode (`create_react_agent`) MUST support tool-calling models with automatic loop cap via `remaining_steps`.
- **FR-003**: Custom mode (`StateGraph`) MUST support Thought → Action → Observation → Final Answer loop.
- **FR-004**: Custom mode MUST support both JSON Action format and text ReAct format.
- **FR-005**: Custom mode MUST cap iterations at `max_iterations` from state.
- **FR-006**: JSON parser MUST accept `name`, `action`, or `tool` as the key for tool identification.
- **FR-007**: JSON parser MUST accept `input`, `arguments`, or `arg` as the key for tool input.
- **FR-008**: Malformed JSON MUST fall back to text format gracefully, not crash.
- **FR-009**: Unrecognisable output format MUST return a format error to the model for retry.
- **FR-010**: `scripts/get_port.py` MUST read `streamlit.port` from `config.yaml` and print it.
- **FR-011**: All three launcher `.bat` files MUST call `get_port.py` to set the port dynamically.
- **FR-012**: `graph_ask()` method MUST be available on `ArgusBrain` and triggerable via `--graph` CLI flag.

### Non-Functional Requirements

- **NFR-001**: All tests MUST pass — unit (10), integration (5), custom mock (1).
- **NFR-002**: Custom mode must handle unknown tools gracefully with error messages.
- **NFR-003**: Custom mode must handle empty LLM responses gracefully.
- **NFR-004**: get_port.py must fail safely (print the canonical default "12199") if config.yaml is missing or unreadable. The fail-safe default MUST equal the configured default so no drift is possible.

---

## Success Criteria

- **SC-001**: Unit tests cover tool map building, target extraction, full cycle, max iterations, unknown tool, immediate Final Answer, empty response, JSON format, JSON variants, and malformed JSON fallback.
- **SC-002**: Integration tests verify Llama 3.1 prebuilt mode, auto-detection, tool map, target extraction, and `brain.graph_ask()`.
- **SC-003**: The `--graph` CLI flag successfully invokes the LangGraph workflow.
- **SC-004**: Changing `config.yaml` port propagates to all launcher scripts.

---

## Key Entities

- `app/core/workflow/graph.py` — `build_workflow()`, `_build_custom_workflow()`, `_build_prebuilt_workflow()`, `_parse_react_output()`, `parse_node()`, `route_after_parse()`, `execute_node()`
- `app/core/workflow/state.py` — `ArgusAgentState`, `ArgusPrebuiltState`
- `app/core/workflow/prompts.py` — `build_react_system_prompt()`
- `app/core/workflow/hooks.py` — `pre_model_hook()`, `post_model_hook()`
- `app/core/brain.py` — `graph_ask()`
- `scripts/get_port.py` — port reader
- `scripts/LAUNCH_STUDIO.bat`, `app/GUI/Launch_Argus.bat`, `app/GUI/Run_Argus_Studio.bat` — launchers
- `config.yaml` — `streamlit.port`
- `tests/test_langgraph_workflow.py` — 10 unit tests
- `workspace/test_full_integration.py` — 5 integration tests
- `workspace/test_custom_mode_with_mock.py` — custom mode test
