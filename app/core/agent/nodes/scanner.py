from app.core.agent.state import AgentState

def scanner_node(state: AgentState) -> AgentState:
    """
    Simulates scanning open ports for specific vulnerabilities.
    """
    print("[Scanner Node] Analyzing open ports for vulnerabilities...")
    
    if 8080 in state["open_ports"]:
        vuln = {"port": 8080, "type": "Mock RCE", "description": "Vulnerable web application detected"}
        state["vulnerabilities"] = [vuln]
        print(f"[Scanner Node] Found vulnerability: {vuln}")
    
    # Initialize the first payload attempt
    state["current_payload"] = "payload_v1"
    
    return state
