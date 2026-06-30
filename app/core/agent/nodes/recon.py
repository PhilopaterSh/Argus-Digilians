from app.core.agent.state import AgentState

def recon_node(state: AgentState) -> AgentState:
    """
    Simulates reconnaissance by identifying open ports.
    """
    print(f"[Recon Node] Scanning target {state['target_ip']}...")
    
    # Mocking discovery of port 8080
    state["open_ports"] = [8080]
    print(f"[Recon Node] Discovered open ports: {state['open_ports']}")
    
    return state
