"""Superseded LangGraph node graph (spec 010: Recon -> Scanner -> Exploit <->
Reflective -> Post-Exploit).

Not the live agent path - `ArgusBrain` drives `react_workflow.py`'s
`build_workflow()` instead (specs 017/018/019). Retained, not deleted, per
Constitution Principle VII (superseded artifacts carry a resolving header
pointing at the canonical replacement). Manually smoke-testable via
`scripts/diagnose_legacy_tactical_graph.py`; not exercised by the pytest
suite except `tests/test_modules/test_tactical_graph_termination.py`, and
does not need to be kept in sync with the live agent's behavior.
"""
import logging

from langgraph.graph import END, StateGraph

from app.core.agent.blackboard import save_entry
from app.core.agent.contracts import record_state_event
from app.core.agent.nodes.exploit import exploit_node
from app.core.agent.nodes.post_exploit import post_exploit_node
from app.core.agent.nodes.recon import recon_node
from app.core.agent.nodes.reflective import reflective_node
from app.core.agent.nodes.scanner import scanner_node
from app.core.agent.state import AgentState
from app.core.config import ArgusConfig

logger = logging.getLogger(__name__)


def _get_max_retries() -> int:
    """Get max retries."""
    try:
        return ArgusConfig.load().max_retries
    except Exception:
        return 3


def self_heal_node(state: AgentState) -> AgentState:
    error_context = "\n".join(state.get("error_log", []))
    logger.warning("[Self-Heal Node] Dependency error or tool failure detected: %s", error_context)
    record_state_event(state, "self_heal", "running", "Attempting self-heal for dependency errors")

    try:
        from app.tools.tool_registry import WSLBridgeTools

        tools = WSLBridgeTools()
        missing_tool = None
        for err in state.get("error_log", []):
            if "not found" in err.lower() or "not installed" in err.lower():
                missing_tool = err.split()[0].strip("':")
                break

        if not missing_tool:
            missing_tool = "nmap"

        heal_result = tools.system_self_heal(missing_tool)
        state["extracted_data"]["self_heal"] = {"tool": missing_tool, "result": heal_result}
        state["last_error"] = heal_result
    except Exception as e:
        logger.error("[Self-Heal Node] Self-healing failed: %s", e)
        state["last_error"] = str(e)

    record_state_event(state, "self_heal", "completed", "Self-heal attempt finished")
    return state


def should_continue(state: AgentState):
    if state.get("exploit_success"):
        return "post_exploit"

    max_retries = _get_max_retries()
    has_dep_error = any(
        "not found" in err.lower() or "not installed" in err.lower() or "permission denied" in err.lower()
        for err in state.get("error_log", [])
    )
    if has_dep_error and state.get("retry_count", 0) < max_retries:
        return "self_heal"

    if state.get("retry_count", 0) >= max_retries or state.get("current_payload") is None:
        save_entry(state["target_ip"], dict(state), "FAILED")
        return END

    return "reflective"


def _route_after_reflective(state: AgentState):
    # reflective_node clears current_payload to None when it exhausts the
    # retry budget (see app/core/agent/nodes/reflective.py), but the old
    # unconditional edge to "exploit" still ran one more, guaranteed-to-fail
    # exploit attempt anyway - producing a confusing trailing
    # "Attempting controlled probe with payload None" / "No payload
    # selected by scanner" pair on every single run that exhausts its
    # retries, even though the real work was already done and reflective's
    # own "Retry budget exhausted" event already explained why.
    if state.get("current_payload") is None:
        save_entry(state["target_ip"], dict(state), "FAILED")
        return END
    return "exploit"


def build_tactical_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("recon", recon_node)
    workflow.add_node("scanner", scanner_node)
    workflow.add_node("exploit", exploit_node)
    workflow.add_node("reflective", reflective_node)
    workflow.add_node("post_exploit", post_exploit_node)
    workflow.add_node("self_heal", self_heal_node)

    workflow.set_entry_point("recon")
    workflow.add_edge("recon", "scanner")
    workflow.add_edge("scanner", "exploit")
    workflow.add_conditional_edges(
        "exploit",
        should_continue,
        {"post_exploit": "post_exploit", "reflective": "reflective", "self_heal": "self_heal", END: END},
    )
    workflow.add_conditional_edges(
        "reflective",
        _route_after_reflective,
        {"exploit": "exploit", END: END},
    )
    workflow.add_edge("self_heal", "exploit")
    workflow.add_edge("post_exploit", END)

    return workflow.compile()
