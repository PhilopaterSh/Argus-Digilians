import logging
import re
from typing import List
from urllib.parse import urlparse

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


def _tech_probe_succeeded(tech_output: str) -> bool:
    """True if whatweb got a real response rather than a runner-level error.

    A failed/timed-out command always surfaces as a string starting with
    "Error:"/"Error (" (see app/tools/command_runner.py); anything else
    means the HTTP request itself actually completed.
    """
    if not tech_output or not tech_output.strip():
        return False
    lowered = tech_output.strip().lower()
    return not (lowered.startswith("error:") or lowered.startswith("error ("))


def _infer_web_port_from_scheme(target: str) -> int:
    parsed = urlparse(target if "://" in target else f"http://{target}")
    return 443 if parsed.scheme == "https" else 80


def recon_node(state: AgentState) -> AgentState:
    target = state["target_ip"]
    mode = state["mode"]
    logger.info("[Recon Node] Scanning target %s...", target)
    record_state_event(state, "recon", "running", f"Starting reconnaissance on {target}")

    state["current_node"] = "recon"
    state["status"] = "running"
    state["updated_at"] = utc_now_iso()

    raw_recon = {}
    try:
        tools = WSLBridgeTools()
        report = tools.recon.recon_suite(target)
        raw_recon = tools.recon.last_recon_results or {}
        ports_output = raw_recon.get("ports", "")

        open_ports = parse_nmap_ports(ports_output)
        state["extracted_data"]["recon_report"] = report
        state["extracted_data"]["raw_recon"] = raw_recon
    except Exception as e:
        # logger.exception() (not .error()) captures the full traceback, not
        # just str(e) - a bare exception message like "[Errno 22] Invalid
        # argument" is nearly useless for diagnosing *where* it came from.
        logger.exception("[Recon Node] Error executing ReconService: %s", e)
        state["error_log"].append(f"Recon failed: {e}")
        state["last_error"] = str(e)
        open_ports = []

    if not open_ports:
        if mode in {AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST}:
            logger.warning("[Recon Node] No open ports discovered. Demo/test fallback enables port 8080.")
            open_ports = [8080]
            state["error_log"].append("Demo/test recon fallback used port 8080")
        elif _tech_probe_succeeded(raw_recon.get("tech", "")):
            # nmap couldn't confirm a port even after the -Pn degraded retry
            # (app/tools/recon.py's recon_suite()) - common behind a
            # WAF/CDN like Cloudflare that blocks/rate-limits port scanning
            # outright. But whatweb got a real HTTP(S) response, so the
            # target is unambiguously a live web target - inferring the
            # scheme's standard port lets scanner/exploit still run instead
            # of the whole pipeline dying because a port-scanner got
            # blocked. Tagged explicitly as inferred, not nmap-confirmed.
            inferred_port = _infer_web_port_from_scheme(target)
            open_ports = [inferred_port]
            state["extracted_data"]["ports_inferred"] = True
            degraded_note = (
                f"nmap could not confirm open ports (likely WAF/CDN blocking the "
                f"scan - see extracted_data.raw_recon.ports); inferred port "
                f"{inferred_port} from the target's URL scheme since whatweb got "
                f"a real HTTP response. Degraded/fallback recon mode."
            )
            logger.warning("[Recon Node] %s", degraded_note)
            state["error_log"].append(degraded_note)
        else:
            state["last_error"] = state.get("last_error") or (
                "No open ports discovered and whatweb got no usable response either "
                "- target appears genuinely unreachable, not just port-scan-blocked"
            )

    state["open_ports"] = open_ports
    state["progress_pct"] = 25 if open_ports else 10
    state["status"] = "running" if open_ports else "failed"
    state["current_node"] = "recon"

    if open_ports:
        if state["extracted_data"].get("ports_inferred"):
            record_state_event(
                state, "recon", "completed",
                f"Reconnaissance phase complete (degraded mode). Inferred port(s): {open_ports}",
            )
        else:
            record_state_event(state, "recon", "completed", f"Reconnaissance phase complete. Open ports: {open_ports}")
    else:
        record_state_event(state, "recon", "failed", state.get("last_error") or "No open ports discovered")

    return state
