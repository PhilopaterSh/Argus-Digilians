from app.core.agent.state import AgentState

def reflective_node(state: AgentState) -> AgentState:
    """
    Analyzes failed attempts and modifies the payload to bypass defenses.
    """
    print("[Reflective Node] WAF or defense detected. Analyzing failure...")
    
    state["retry_count"] += 1
    
    # Simulate modifying the payload
    if "payload_v1" in state["failed_payloads"]:
        print("[Reflective Node] Modifying payload to payload_v2 (obfuscated)...")
        state["current_payload"] = "payload_v2"
    else:
        print("[Reflective Node] Unable to determine bypass strategy.")
        state["current_payload"] = None

    return state
