# Implementation Plan: LangGraph Workflow — Final (Research-Backed)

**Branch**: `main` | **Date**: 2026-07-05

---

## Summary

Replace the current linear tool-execution loop (`_run_tools_direct()`) with a **LangGraph ReAct agent** using `create_react_agent` from `langgraph.prebuilt`. The prebuilt agent handles the core LLM ↔ tools loop natively. We layer on custom `state_schema`, `pre_model_hook`, `post_model_hook`, and a **wrapping custom StateGraph** for pre/post processing, blackboard management, and error recovery — all without rewriting the ReAct loop from scratch.

---

## Research Findings

### 1. Current code is 3× deprecated

| Current import | Status | Correct alternative |
|---|---|---|
| `from langchain_classic.agents import create_react_agent` | ❌ Legacy (pre-v1) | `langgraph.prebuilt.create_react_agent` or custom `StateGraph` |
| `from langchain.agents import create_react_agent` | ⚠️ Deprecated in v1 | `langchain.agents.create_agent` |
| `from langgraph.prebuilt import create_react_agent` | ✅ Stable, streaming support | What we use |

### 2. Prebuilt `create_react_agent` internal graph structure

```
START → [pre_model_hook?] → agent (LLM) → [post_model_hook?] → conditional_router
                                                                  ├── tool_calls → tools → (back to agent)
                                                                  └── no_tool_calls → END
```

### 3. Custom state schema works (proven in production)

```python
class ArgusAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # required
    remaining_steps: int                                    # required (built-in loop cap)
    # ── custom fields ──
    target: str
    phase: str                                              # init|recon|discovery|exploit|report
    blackboard_summary: str
    last_tool_name: Optional[str]
    last_tool_error: Optional[str]
    findings: Annotated[list[dict], add]                   # accumulated findings
    iteration_count: int
```

### 4. `pre_model_hook` injects blackboard before EVERY LLM call

Signature: `(state: ArgusAgentState) -> dict`  
Returns: `{"messages": [new_messages...], "llm_input_messages": [...], ...}`

This is how the LLM sees the **live blackboard** as context on every turn — exactly as you described.

### 5. `post_model_hook` saves results after every LLM response

Signature: `(state: ArgusAgentState) -> dict`  
Runs after LLM produces a response but before tools execute. Used for:
- Saving the LLM's decision to SQLite
- Updating blackboard summary
- Detecting loops (same tool 3× → force END)

### 6. `ToolNode` has built-in error handling

```python
ToolNode(tools, handle_tool_errors=True)  # catches exceptions → ToolMessage
```

When a tool fails (e.g., Curl timeout), the error message goes back to the LLM as a regular observation. The LLM **naturally decides** to retry with different params or try an alternative tool. No extra error handler node needed.

### 7. Adding custom nodes is done by wrapping in a parent StateGraph

You can't modify `create_react_agent`'s internal nodes. But you can:

```python
parent = StateGraph(ParentState)
parent.add_node("init", init_node)
parent.add_node("agent", react_agent)  # subgraph
parent.add_node("report", report_node)

parent.add_edge(START, "init")
parent.add_edge("init", "agent")
parent.add_conditional_edges("agent", check_done, {"report": "report", "agent": "agent"})
parent.add_edge("report", END)
```

This is the **advanced** path. For v1, we start with just `create_react_agent` + hooks.

---

## Architecture v2 (Final)

### Phase 1: Core ReAct agent with custom state + hooks (minimal)

```
create_react_agent(
    model,
    tools,
    state_schema=ArgusAgentState,
    prompt=inject_blackboard_prompt,    # adds blackboard + phase to system message
    pre_model_hook=refresh_blackboard,   # updates blackboard_summary before each LLM call
    post_model_hook=save_findings,       # saves results to SQLite after each LLM response
)
```

| Component | What it does |
|-----------|-------------|
| `ArgusAgentState` | Carries `target`, `phase`, `blackboard_summary`, `findings[]`, `last_tool_error`, `iteration_count` |
| `prompt` (callable) | Dynamically builds system message with current phase + blackboard context |
| `pre_model_hook` | Refreshes `blackboard_summary` from SQLite before LLM sees it |
| `post_model_hook` | After LLM produces output, saves findings to SQLite before tools execute |

### Phase 2: Wrap in parent StateGraph for pre/post processing (full)

```
[init] → [agent (subgraph)] → [report]
                                  ↑
                             [save_state] ── (loop back if more work needed)
```

| Custom node | Purpose |
|-------------|---------|
| `init` | Extract target from query, init SQLite connection, set initial phase |
| `agent` | The compiled `create_react_agent` — handles the full ReAct loop internally |
| `save_state` | After agent finishes, compute final blackboard summary |
| `report` | Generate `SecurityReport` JSON using existing Pydantic schema |
| `decide_continue` | Conditional edge: if findings sufficient → report, else → agent again |

### Tool error flow (no custom code needed)

```
LLM decides: Run_FFUF
  → ToolNode executes FFUF
  → FFUF crashes (timeout)
  → ToolNode catches error → ToolMessage(content="Error: timeout")
  → LLM sees error in messages
  → LLM naturally decides: "FFUF failed, let me try Nikto instead"
  → LLM calls Run_Nikto → success
```

### Blackboard update flow (via pre/post hooks)

```
1. pre_model_hook:
   - Reads `argus_intelligence.db` via ArgusMemory.get_blackboard_summary()
   - Updates `state["blackboard_summary"]`
   - Returns {"blackboard_summary": updated_value}

2. The system prompt (callable) then includes it:
   SystemMessage(f"""Current Phase: {state['phase']}
   Blackboard Intelligence:
   {state['blackboard_summary']}

   Available tools: {tool_descriptions}
   Choose the next tool or say you're done.""")
```

---

## Comparison: Old vs New

| Aspect | Old (Linear) | New (LangGraph) |
|--------|-------------|-----------------|
| **Tool execution** | ALL 15+ tools, sequential | LLM decides 1 tool at a time |
| **Blackboard** | Read once at start | Refreshed before EVERY LLM call |
| **Error handling** | `except: pass` + continue | ToolNode catches → LLM sees error → decides retry/alternative |
| **Loop control** | None | `remaining_steps` built-in + `iteration_count` custom |
| **LLM calls per run** | 1 | ~5-15 (one per decision step) |
| **GUI streaming** | Not supported | `astream_events()` for real-time thoughts |
| **Code complexity** | ~50 lines in brain.py | ~100 lines across 4 new files |
| **Backward compat** | — | `ask()` untouched; `graph_ask()` added |

---

## File Structure

### Modified files

| File | Change |
|------|--------|
| `app/core/brain.py` | Add `graph_ask()` method uses LangGraph |
| `app/core/prompts.py` | Add `build_langgraph_prompt(state)` callable |
| `run_argus_cli.py` | Add `--graph` flag |
| `app/GUI/app.py` | Add toggle for graph mode |
| `requirements.txt` | Add `langgraph>=0.2.0` |

### New files

| File | Purpose |
|------|---------|
| `app/core/workflow/__init__.py` | Package init |
| `app/core/workflow/state.py` | `ArgusAgentState` TypedDict |
| `app/core/workflow/graph.py` | `build_workflow()` — builds + compiles the full graph |
| `app/core/workflow/hooks.py` | `pre_model_hook()` and `post_model_hook()` functions |
| `app/core/workflow/prompt.py` | `build_system_prompt(state)` — callable for dynamic prompt |
| `tests/test_langgraph_workflow.py` | Unit tests |

---

## Dependencies

```
langgraph>=0.2.0,<0.5.0
```

Already present (no changes needed):
- `langchain-core` (for BaseMessage, ToolMessage, SystemMessage, etc.)
- `langchain-ollama` (for OllamaLLM with bind_tools)
- `langgraph.prebuilt` (bundled with langgraph)
