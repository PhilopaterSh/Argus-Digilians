# Tasks: LangGraph Workflow Implementation

**Input**: Plan at `.opencode/plans/003-langgraph-workflow-plan.md`

---

## Phase 0: Research & Environment

**Purpose**: Verify dependencies and confirm the approach works with Ollama + existing tools.

- [ ] T001 Read existing `requirements.txt` / `pyproject.toml` — check if `langgraph` is already listed, verify `langchain-ollama` is present
- [ ] T002 Quick test: create a minimal `create_react_agent` with Ollama + 1 mock tool, verify it runs in current Python env
- [ ] T003 Verify `llm.bind_tools(tools)` works with `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B` via Ollama
- [ ] T004 Confirm `ToolNode.handle_tool_errors=True` catches and wraps tool exceptions correctly

---

## Phase 1: State Schema

**Purpose**: Define the custom `ArgusAgentState` TypedDict.

- [ ] T005 Create `app/core/workflow/state.py`:
  ```python
  class ArgusAgentState(TypedDict):
      messages: Annotated[list[BaseMessage], add_messages]
      remaining_steps: int                # built-in loop cap (default 30)
      target: str
      phase: str                          # init | recon | discovery | exploit | report
      blackboard_summary: str
      last_tool_name: Optional[str]
      last_tool_error: Optional[str]
      findings: Annotated[list[dict], add]
      iteration_count: int
  ```

---

## Phase 2: Dynamic System Prompt

**Purpose**: Build a callable that generates the system message including blackboard + phase.

- [ ] T006 Create `app/core/workflow/prompt.py`:
  - Function `build_system_prompt(state: ArgusAgentState) -> list[BaseMessage]`
  - Returns `[SystemMessage(f"Phase: {phase}\nBlackboard: {blackboard}\nTools: ...")] + state["messages"]`
  - Uses existing tool descriptions from `tool_registry.py`
  - Includes phase-specific instructions (e.g., in recon phase: focus on subdomains)

---

## Phase 3: Hooks

**Purpose**: Implement `pre_model_hook` (refresh blackboard) and `post_model_hook` (save findings).

- [ ] T007 Create `app/core/workflow/hooks.py`:
  - `pre_model_hook(state: ArgusAgentState) -> dict`:
    - Calls `ArgusMemory.get_blackboard_summary()` to refresh `blackboard_summary`
    - Increments `iteration_count`
    - Returns `{"blackboard_summary": new_value, "iteration_count": new_count}`
  - `post_model_hook(state: ArgusAgentState) -> dict`:
    - After LLM produces a response, extract tool call info
    - If a tool was called, save the intent to SQLite via `ArgusMemory.add_finding()`
    - Loop detection: if same tool name appears 3+ times in last 6 messages, set `remaining_steps = 0` (forces END)

---

## Phase 4: Graph Assembly

**Purpose**: Wire everything into a compiled graph.

- [ ] T008 Create `app/core/workflow/__init__.py` — exports `build_workflow()`
- [ ] T009 Create `app/core/workflow/graph.py`:
  ```
  def build_workflow(llm, tools: list, memory: ArgusMemory) -> CompiledStateGraph:
      # 1. Bind tools to LLM
      llm_with_tools = llm.bind_tools(tools)

      # 2. Build core ReAct agent
      react_agent = create_react_agent(
          model=llm_with_tools,
          tools=tools,
          state_schema=ArgusAgentState,
          prompt=build_system_prompt,
          pre_model_hook=pre_model_hook,
          post_model_hook=post_model_hook,
          version="v2",
      )

      # 3. Wrap in parent StateGraph
      parent = StateGraph(ArgusAgentState)

      parent.add_node("init", init_node)        # extract target, init memory
      parent.add_node("agent", react_agent)      # subgraph
      parent.add_node("report", report_node)      # generate SecurityReport JSON

      parent.add_edge(START, "init")
      parent.add_edge("init", "agent")
      parent.add_conditional_edges("agent", check_done, {
          "report": "report",
          "continue": "agent",
      })
      parent.add_edge("report", END)

      return parent.compile()
  ```

### Sub-nodes (inside `graph.py`):

- [ ] T010 `init_node(state) -> dict`:
  - Extract `target` from user messages (parse URL)
  - Call `ArgusMemory.upsert_target(target)` to register in DB
  - Set `phase = "init"`, `iteration_count = 0`
  - Return `{"target": ..., "phase": ..., ...}`

- [ ] T011 `report_node(state) -> dict`:
  - Build `SecurityReport` Pydantic object from `state["findings"]`
  - Call LLM one final time to generate structured JSON
  - Return `{"final_report": json_report}`

- [ ] T012 `check_done(state) -> str`:
  - If `remaining_steps <= 0` or `iteration_count >= 30` → `"report"`
  - If `phase == "report"` → `"report"`
  - Else → `"continue"`

---

## Phase 5: Integration with ArgusBrain

**Purpose**: Add `graph_ask()` to `ArgusBrain`, connect CLI and GUI.

- [ ] T013 Add `graph_ask(query: str)` to `app/core/brain.py`:
  ```python
  def graph_ask(self, query: str) -> Dict[str, Any]:
      from app.core.workflow.graph import build_workflow
      graph = build_workflow(self.llm, list(self.tool_map.values()), self.memory)
      initial = ArgusAgentState(
          messages=[HumanMessage(content=query)],
          remaining_steps=30,
          target="",
          phase="init",
          blackboard_summary=self._blackboard_context or "",
          last_tool_name=None,
          last_tool_error=None,
          findings=[],
          iteration_count=0,
      )
      final = graph.invoke(initial)
      return self._process_output(final.get("final_report", ""))
  ```

- [ ] T014 Add `--graph` flag to `run_argus_cli.py` — calls `brain.graph_ask()` when set
- [ ] T015 Add toggle in `app/GUI/app.py` — checkbox for "Use LangGraph workflow"

---

## Phase 6: Testing

- [ ] T016 Create `tests/test_langgraph_workflow.py`:
  - Test `ArgusAgentState` schema — instantiate and validate
  - Test `pre_model_hook` with mock `ArgusMemory` — verify it updates `blackboard_summary`
  - Test `post_model_hook` — verify it saves findings and detects loops
  - Test `check_done` — verify routing logic for all conditions
  - Integration test: mock LLM + mock tools, run full graph, verify flow
- [ ] T017 Run `python -m pytest tests/test_langgraph_workflow.py -v` — all green
- [ ] T018 Manual end-to-end: `python run_argus_cli.py --graph https://test.com` — verify it works end-to-end

---

## Phase 7: Edge Cases

- [ ] T019 `remaining_steps=0` → graph should route to `report` immediately (no infinite loops)
- [ ] T020 ToolNode error: if ALL tools fail → LLM should still produce a report saying "all tools failed"
- [ ] T021 Empty findings: if no tools were called (LLM decides directly) → still produce valid SecurityReport
- [ ] T022 KeyboardInterrupt: graph should save partial state to SQLite before exiting

---

## Execution Order

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
```

---

## Summary

| Metric | Value |
|--------|-------|
| New files | 6 |
| Modified files | 4 |
| Core ReAct loop | Provided by `create_react_agent` (zero custom code) |
| Custom code | Prompts, hooks, wrapper nodes |
| Risk to existing code | None — `ask()` untouched, `graph_ask()` is additive |
| LLM calls per run | Tool count + 1 (vs 1 call currently) |
| Error handling | ToolNode built-in + LLM natural language recovery |
