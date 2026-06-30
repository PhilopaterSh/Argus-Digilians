import logging
from app.core.agent.state import AgentState

logger = logging.getLogger(__name__)

def scanner_node(state: AgentState) -> AgentState:
    """
    Simulates scanning open ports for specific vulnerabilities.
    """
    logger.info("[Scanner Node] Analyzing open ports for vulnerabilities...")
    
    if 8080 in state["open_ports"]:
        vuln = {"port": 8080, "type": "Mock RCE", "description": "Vulnerable web application detected"}
        state["vulnerabilities"] = [vuln]
        logger.info("[Scanner Node] Found vulnerability: %s", vuln)
    
    # Initialize the first payload attempt
    state["current_payload"] = "payload_v1"
    
    return state

