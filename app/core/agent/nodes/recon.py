import logging
import re
from app.core.agent.state import AgentState
from app.tools.tool_registry import WSLBridgeTools

logger = logging.getLogger(__name__)

def parse_nmap_ports(nmap_output: str) -> list[int]:
    ports = []
    if not nmap_output:
        return ports
    # Regex to find open ports in nmap stdout (e.g. 80/tcp open http)
    pattern = re.compile(r"(\d+)/tcp\s+open")
    for match in pattern.finditer(nmap_output):
        ports.append(int(match.group(1)))
    return ports

def recon_node(state: AgentState) -> AgentState:
    """
    Executes reconnaissance on the target IP/domain and identifies open ports using ReconService.
    """
    target = state["target_ip"]
    logger.info("[Recon Node] Scanning target %s...", target)
    
    try:
        tools = WSLBridgeTools()
        tools.recon.recon_suite(target)
        
        # Parse the ports output from the recon suite nmap scan
        ports_output = ""
        if tools.recon.last_recon_results and "ports" in tools.recon.last_recon_results:
            ports_output = tools.recon.last_recon_results["ports"]
            
        open_ports = parse_nmap_ports(ports_output)
    except Exception as e:
        logger.error("[Recon Node] Error executing ReconService: %s", e)
        open_ports = []
    
    # Fallback to simulated/default port 8080 if scan returns empty
    if not open_ports:
        logger.warning("[Recon Node] No open ports discovered via Nmap. Falling back to default port 8080.")
        open_ports = [8080]
        
    state["open_ports"] = open_ports
    logger.info("[Recon Node] Discovered open ports: %s", state["open_ports"])
    
    return state

