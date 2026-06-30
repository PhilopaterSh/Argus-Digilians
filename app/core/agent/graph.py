import logging
from langgraph.graph import StateGraph, END
from app.core.agent.state import AgentState
from app.core.agent.nodes.recon import recon_node
from app.core.agent.nodes.scanner import scanner_node
from app.core.agent.nodes.exploit import exploit_node
from app.core.agent.nodes.reflective import reflective_node
from app.core.agent.nodes.post_exploit import post_exploit_node
from app.core.agent.blackboard import save_entry
from app.core.config import ArgusConfig

logger = logging.getLogger(__name__)

# Load config to get max retries setting
try:
    config = ArgusConfig.load()
    MAX_RETRIES = config.max_retries
except Exception:
    MAX_RETRIES = 3

def self_heal_node(state: AgentState) -> AgentState:
    """
    Error handler node that attempts to self-heal missing dependencies.
    """
    error_context = "\n".join(state["error_log"]) if state["error_log"] else ""
    logger.warning("[Self-Heal Node] Dependency error or tool failure detected: %s", error_context)
    
    try:
        from app.tools.tool_registry import WSLBridgeTools
        tools = WSLBridgeTools()
        
        # Analyze error_log for common missing tool indicators
        missing_tool = None
        for err in state["error_log"]:
            if "not found" in err.lower() or "not installed" in err.lower():
                parts = err.split()
                for p in parts:
                    if p.endswith(":") or p.startswith("'"):
                        clean_p = p.strip("':")
                        if clean_p and clean_p != "command":
                            missing_tool = clean_p
                            break
        
        if not missing_tool:
            # Fallback/generic heal target
            missing_tool = "nmap"
            
        logger.info("[Self-Heal Node] Attempting self-heal for: %s", missing_tool)
        heal_result = tools.self_heal.system_self_heal(missing_tool)
        logger.info("[Self-Heal Node] Result: %s", heal_result)
        
        # Record self-heal attempt in messages
        from langchain_core.messages import SystemMessage
        state["messages"] = [
            SystemMessage(content=f"Self-heal attempt for {missing_tool}: {heal_result}")
        ]
    except Exception as e:
        logger.error("[Self-Heal Node] Self-healing failed: %s", e)
        
    return state

def should_continue(state: AgentState):
    """
    Routing logic after an exploit attempt.
    """
    if state["exploit_success"]:
        return "post_exploit"
        
    # Check if there is a dependency / environment error requiring self healing
    has_dep_error = any(
        "not found" in err.lower() or "not installed" in err.lower() or "permission denied" in err.lower()
        for err in state.get("error_log", [])
    )
    if has_dep_error and state.get("retry_count", 0) < MAX_RETRIES:
        logger.info("[System] Dependency error detected. Routing to Self-Heal Node.")
        return "self_heal"
    
    if state["retry_count"] >= MAX_RETRIES or state["current_payload"] is None:
        logger.info("[System] Max retries reached or no payload. Aborting.")
        save_entry(state["target_ip"], state, "FAILED")
        return END
        
    return "reflective"

def build_tactical_graph():
    """
    Compiles the stateful LangGraph for the tactical pentest agent.
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("recon", recon_node)
    workflow.add_node("scanner", scanner_node)
    workflow.add_node("exploit", exploit_node)
    workflow.add_node("reflective", reflective_node)
    workflow.add_node("post_exploit", post_exploit_node)
    workflow.add_node("self_heal", self_heal_node)
    
    # Define edges
    workflow.set_entry_point("recon")
    workflow.add_edge("recon", "scanner")
    workflow.add_edge("scanner", "exploit")
    
    # Conditional edge after exploit
    workflow.add_conditional_edges(
        "exploit",
        should_continue,
        {
            "post_exploit": "post_exploit",
            "reflective": "reflective",
            "self_heal": "self_heal",
            END: END
        }
    )
    
    # Cycle back to exploit after reflection
    workflow.add_edge("reflective", "exploit")
    
    # Retry exploit after self healing
    workflow.add_edge("self_heal", "exploit")
    
    # End after post-exploit
    workflow.add_edge("post_exploit", END)
    
    return workflow.compile()

