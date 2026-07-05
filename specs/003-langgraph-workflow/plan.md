# Implementation Plan: LangGraph Workflow + JSON Parser + Config-Driven Port

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-07-05 | **Spec**: `specs/003-langgraph-workflow/spec.md`

**Status**: ✅ Completed

---

## Summary

Build a LangGraph workflow for Argus that supports both tool_calling models (Llama 3.1) and non-tool-calling models (WhiteRabbitNeo). The workflow auto-detects model capability and routes to either `create_react_agent` (prebuilt) or a custom text-ReAct `StateGraph`. Integrate a dual-format parser (JSON Action + text ReAct) and make the Streamlit port configurable from `config.yaml`.

---

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: langgraph>=0.2.0, langchain-ollama, langchain-core, pyyaml

**Storage**: None (stateless workflow; state managed in-memory via LangGraph)

**Testing**: pytest with mock LLM and tool fixtures

**Target Platform**: Windows with WSL/Kali Linux backend

**Project Type**: CLI/GUI AI penetration testing framework

### Architecture

```text
build_workflow(llm, tools)
  │
  ├─ _supports_tool_calls(llm) → True
  │   └─ _build_prebuilt_workflow(llm, tools, tool_map)
  │       └─ create_react_agent(model, tools, ..., hooks)
  │
  └─ _supports_tool_calls(llm) → False
      └─ _build_custom_workflow(llm, tools, tool_map)
          └─ StateGraph(ArgusAgentState)
              ├─ agent_node → parse_node
              ├─ parse_node → execute_node (or agent on error, or END on Final Answer)
              └─ execute_node → agent (or END on max_iterations)
```

### Parser Dual-Format

```text
_parse_react_output(content, default_input)
  ├─ 1. Check for "Final Answer:" → phase="done"
  ├─ 2. Try JSON regex → json.loads → extract name + input
  ├─ 3. Fallback text regex → extract Action + Action Input
  └─ 4. Nothing detected → tool_error with format guidance
```

### Config-Driven Port

```text
scripts/get_port.py
  └─ reads config.yaml → streamlit.port → prints to stdout

scripts/LAUNCH_STUDIO.bat
app/GUI/Launch_Argus.bat
app/GUI/Run_Argus_Studio.bat
  └─ for /f %%p in ('python get_port.py') do set PORT=%%p
  └─ streamlit run ... --server.port %PORT%
```

---

## Constitution Check

*GATE: Passed — no violations.*

---

## Project Structure

```text
specs/003-langgraph-workflow/
├── spec.md       # This file
├── plan.md       # This file
└── tasks.md      # Completed tasks

app/core/workflow/
├── __init__.py
├── graph.py      # Core workflow builder, parser, nodes, routers
├── state.py      # TypedDict state schemas
├── prompts.py    # System prompt builders
└── hooks.py      # Pre/post model hooks

scripts/
├── get_port.py   # Port reader from config.yaml
├── LAUNCH_STUDIO.bat  # Updated to use dynamic port
└── ...

app/GUI/
├── Launch_Argus.bat       # Updated to use dynamic port
└── Run_Argus_Studio.bat   # Updated to use dynamic port

tests/
└── test_langgraph_workflow.py  # 10 unit tests

workspace/
├── test_full_integration.py         # 5 integration tests
└── test_custom_mode_with_mock.py    # Custom mode loop test
```

---

## Phases & Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Research LangGraph API compatibility | ✅ Done |
| 1 | Build workflow package (state, graph, hooks, prompts) | ✅ Done |
| 2 | Implement dual-format parser (JSON + text) | ✅ Done |
| 3 | Implement format error recovery | ✅ Done |
| 4 | Create `graph_ask()` on `ArgusBrain` | ✅ Done |
| 5 | Add `--graph` CLI flag | ✅ Done |
| 6 | Create `get_port.py` and update launchers | ✅ Done |
| 7 | Write unit tests (10) | ✅ Done |
| 8 | Write integration tests (5 + 1 custom mock) | ✅ Done |
| 9 | Update AGENTS.md with progress log | ✅ Done |
