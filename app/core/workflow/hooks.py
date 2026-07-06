"""Pre/post model hooks for the create_react_agent path.

These hooks refresh the blackboard before each LLM call
and save findings after each LLM response.
"""
from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES


def pre_model_hook(state: dict) -> dict:
    """Refresh blackboard summary before each LLM call.

    Called by create_react_agent before the 'agent' node.
    Injects latest intelligence from SQLite into graph state.
    """
    update = {
        "iteration_count": state.get("iteration_count", 0) + 1,
    }

    memory = state.get("_memory")
    if memory is not None:
        try:
            summary = memory.get_blackboard_summary()
            if summary and summary != "{}":
                update["blackboard_summary"] = summary
        except Exception:
            pass

    return update


def post_model_hook(state: dict) -> dict:
    """Save findings after each LLM response.

    Called by create_react_agent after the 'agent' node.
    Persists tool call intents to SQLite.
    """
    last = state["messages"][-1] if state["messages"] else None
    if last is None:
        return {}

    memory = state.get("_memory")
    target = state.get("target", "unknown")

    if memory is not None and hasattr(last, "tool_calls") and last.tool_calls:
        for tc in last.tool_calls:
            try:
                memory.add_finding(
                    domain=target,
                    tool_name=tc.get("name", "unknown"),
                    data_type="llm_decision",
                    raw_data=str(tc.get("args", {})),
                    summary=f"LLM chose tool {tc['name']} with args {tc['args']}",
                )
            except Exception:
                pass

    return {}
