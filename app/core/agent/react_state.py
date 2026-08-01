"""State definitions for Argus LangGraph workflows.

Two state schemas:
- ArgusAgentState: Shared base for both modes.
- ArgusPrebuiltState: Used with create_react_agent (requires remaining_steps).
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import NotRequired


class ArgusAgentState(TypedDict):
    """Shared state for the custom text-based ReAct graph.

    Works with ANY model (no tool_calls requirement).
    """
    messages: Annotated[list[BaseMessage], add_messages]
    target: str
    phase: str
    blackboard_summary: str
    iteration_count: int
    max_iterations: int
    tool_name: Optional[str]
    tool_input: Optional[str]
    tool_result: Optional[str]
    tool_error: Optional[str]
    tool_call_history: list[str]
    reflection_notes: list[str]
    phase56_nudged: bool
    # 2026-07-26: whether the one-time "you gave a Final Answer without
    # executing a single tool" nudge (react_workflow.py::parse_node) has
    # already fired this run - live-discovered TWICE independently (a
    # PortSwigger lab, then a real production site) where the model wrote
    # "Final Answer:" on its very first turn with zero tool calls, and the
    # resulting report contained fabricated findings with no real evidence
    # behind them (Constitution VIII violation). Mirrors phase56_nudged's
    # own one-time-per-run design.
    zero_tool_final_answer_nudged: bool
    # 2026-07-26: whether the one-time "you called some tool(s) but skipped
    # Phase 1-2 (connectivity/recon)" nudge has already fired this run -
    # companion to zero_tool_final_answer_nudged above, mirrors
    # phase56_nudged's own one-time-per-run design.
    phase12_nudged: bool
    # 2026-07-25: consecutive duplicate_call blocks in a row (reset to 0 on
    # any genuine tool execution) - once this reaches
    # react_workflow.py::MAX_CONSECUTIVE_DUPLICATE_BLOCKS, the run concludes
    # early with an honest partial Final Answer instead of silently burning
    # the rest of max_iterations on a conversation that provably cannot
    # change outcome (the duplicate-call guard's own hard block guarantees
    # the same guidance every subsequent identical/oscillating attempt).
    consecutive_duplicate_blocks: NotRequired[int]
    # specs/020 (multi-agent role separation, feature-flagged off by default -
    # see config.yaml's enable_multi_agent_roles): only populated when the
    # multi-role graph (react_workflow.py::build_multi_role_workflow) is in
    # use; the single-loop graph never sets these.
    current_role: NotRequired[str]
    role_history: NotRequired[list[str]]


class ArgusPrebuiltState(ArgusAgentState):
    """Extended state for use with create_react_agent.

    Requires remaining_steps (built-in loop cap).
    Uses custom fields from ArgusAgentState via hooks.
    """
    remaining_steps: int
