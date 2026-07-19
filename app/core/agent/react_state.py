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
