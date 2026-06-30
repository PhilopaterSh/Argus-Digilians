from langgraph.graph import StateGraph, END
from app.core.agent.state import AgentState
from app.core.agent.nodes.recon import recon_node
from app.core.agent.nodes.scanner import scanner_node
from app.core.agent.nodes.exploit import exploit_node
from app.core.agent.nodes.reflective import reflective_node
from app.core.agent.nodes.post_exploit import post_exploit_node
from app.core.agent.blackboard import save_entry

def should_continue(state: AgentState):
    """
    Routing logic after an exploit attempt.
    """
    if state["exploit_success"]:
        return "post_exploit"
    
    if state["retry_count"] >= 3 or state["current_payload"] is None:
        print("[System] Max retries reached or no payload. Aborting.")
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
            END: END
        }
    )
    
    # Cycle back to exploit after reflection
    workflow.add_edge("reflective", "exploit")
    
    # End after post-exploit
    workflow.add_edge("post_exploit", END)
    
    return workflow.compile()
