# Tasks: LangGraph Workflow + JSON Parser + Config-Driven Port

**Status**: ✅ All tasks completed

**Input**: `specs/003-langgraph-workflow/spec.md`, `specs/003-langgraph-workflow/plan.md`

---

## Phase 1: Core Workflow Package

- [x] T001 Create `app/core/workflow/__init__.py`
- [x] T002 Create `app/core/workflow/state.py` with `ArgusAgentState` and `ArgusPrebuiltState`
- [x] T003 Create `app/core/workflow/graph.py` with `build_workflow()`, `_supports_tool_calls()`, `_build_prebuilt_workflow()`, `_build_custom_workflow()`
- [x] T004 Create `app/core/workflow/prompts.py` with `build_react_system_prompt()` and `build_prebuilt_system_prompt()`
- [x] T005 Create `app/core/workflow/hooks.py` with `pre_model_hook()` and `post_model_hook()`

## Phase 2: Dual-Format Parser

- [x] T006 Implement `_parse_react_output()` with JSON-first, text-fallback logic in `graph.py`
- [x] T007 Support JSON keys: `name`, `action`, `tool`, `input`, `arguments`, `arg`
- [x] T008 Implement format error recovery — parser returns error message when no format detected
- [x] T009 Update `route_after_parse()` to send format errors back to agent for retry

## Phase 3: Brain Integration

- [x] T010 Add `graph_ask()` method to `ArgusBrain` in `app/core/brain.py`
- [x] T011 Add `--graph` CLI flag in `run_argus_cli.py`

## Phase 4: Config-Driven Port

- [x] T012 Create `scripts/get_port.py` — reads `streamlit.port` from `config.yaml`
- [x] T013 Update `scripts/LAUNCH_STUDIO.bat` to use dynamic port
- [x] T014 Update `app/GUI/Launch_Argus.bat` to use dynamic port
- [x] T015 Update `app/GUI/Run_Argus_Studio.bat` to use dynamic port
- [x] T016 Change `config.yaml` port from `8501` to `8199`

## Phase 5: Testing

- [x] T017 Write test: tool map building
- [x] T018 Write test: target extraction
- [x] T019 Write test: custom graph full cycle (scan → search → final)
- [x] T020 Write test: stops at max iterations
- [x] T021 Write test: handles unknown tool
- [x] T022 Write test: immediate Final Answer
- [x] T023 Write test: empty LLM response
- [x] T024 Write test: JSON Action format
- [x] T025 Write test: JSON alternative key variants
- [x] T026 Write test: malformed JSON fallback to text
- [x] T027 Write integration test: prebuilt mode with Llama 3.1
- [x] T028 Write integration test: auto-detection of model capabilities
- [x] T029 Write integration test: tool map building
- [x] T030 Write integration test: target extraction
- [x] T031 Write integration test: brain.graph_ask()
- [x] T032 Write custom mode loop test with mock LLM

## Phase 6: Documentation

- [x] T033 Update AGENTS.md with progress log
- [x] T034 Create Speckit spec, plan, and tasks for the feature
