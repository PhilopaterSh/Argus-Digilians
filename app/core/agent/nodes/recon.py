import logging
import re
from typing import List

from app.core.agent.contracts import AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST, record_state_event, utc_now_iso
from app.core.agent.state import AgentState
from app.tools.tool_registry import WSLBridgeTools

logger = logging.getLogger(__name__)


def parse_nmap_ports(nmap_output: str) -> List[int]:
    ports = []
    if not nmap_output:
        return ports
    pattern = re.compile(r"(\d+)/tcp\s+open")
    for match in pattern.finditer(nmap_output):
        ports.append(int(match.group(1)))
    return ports


def recon_node(state: AgentState) -> AgentState:
    target = state["target_ip"]
    mode = state["mode"]
    logger.info("[Recon Node] Scanning target %s...", target)
    record_state_event(state, "recon", "running", f"Starting reconnaissance on {target}")

    state["current_node"] = "recon"
    state["status"] = "running"
    state["updated_at"] = utc_now_iso()

    try:
        tools = WSLBridgeTools()
        report = tools.recon.recon_suite(target)
        ports_output = ""
        if tools.recon.last_recon_results and "ports" in tools.recon.last_recon_results:
            ports_output = tools.recon.last_recon_results["ports"]

        open_ports = parse_nmap_ports(ports_output)
        state["extracted_data"]["recon_report"] = report
        state["extracted_data"]["raw_recon"] = tools.recon.last_recon_results or {}
    except Exception as e:
        logger.error("[Recon Node] Error executing ReconService: %s", e)
        state["error_log"].append(f"Recon failed: {e}")
        state["last_error"] = str(e)
        open_ports = []

    if not open_ports:
        if mode in {AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST}:
            logger.warning("[Recon Node] No open ports discovered. Demo/test fallback enables port 8080.")
            open_ports = [8080]
            state["error_log"].append("Demo/test recon fallback used port 8080")
        else:
            state["last_error"] = state.get("last_error") or "No open ports discovered"

    state["open_ports"] = open_ports
    state["progress_pct"] = 25 if open_ports else 10
    state["status"] = "running" if open_ports else "failed"
    state["current_node"] = "recon"

    if open_ports:
        record_state_event(state, "recon", "completed", f"Reconnaissance phase complete. Open ports: {open_ports}")
    else:
        record_state_event(state, "recon", "failed", "No open ports discovered")

    return state
