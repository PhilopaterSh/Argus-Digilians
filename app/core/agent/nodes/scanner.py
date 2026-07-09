import logging

from app.core.agent.contracts import record_state_event, utc_now_iso
from app.core.agent.nodes._shared import _build_target_url, _first_web_port
from app.core.agent.state import AgentState
from app.tools.tool_registry import WSLBridgeTools

logger = logging.getLogger(__name__)


def scanner_node(state: AgentState) -> AgentState:
    """Scan the recon-discovered web port for vulnerabilities (nikto/ffuf).

    Args:
        state (AgentState): Current graph state; reads `open_ports` (from
            `recon_node`) and `target_ip`, falling back to a scheme-inferred
            port (443/80) if recon confirmed none.

    Returns:
        AgentState: The same state, updated with `vulnerabilities`,
        `current_payload` (selected for `exploit_node`), and
        `extracted_data["scanner"]`.
    """
    logger.info("[Scanner Node] Analyzing open ports for vulnerabilities...")
    record_state_event(state, "scanner", "running", "Starting vulnerability scanning")
    state["current_node"] = "scanner"
    state["status"] = "running"
    state["updated_at"] = utc_now_iso()

    web_port = _first_web_port(state.get("open_ports", []))
    target_ip = state["target_ip"]

    if not web_port:
        # recon_node may have found zero confirmed ports (nmap timeout, or a
        # WAF/CDN like Cloudflare blocking the scan outright - see
        # app/core/agent/nodes/recon.py's own scheme-inference fallback,
        # which itself can still come up empty on a transport-level
        # failure). Don't hard-block scanning on that single failure point:
        # if the target itself is an http(s) URL, it's unambiguously a web
        # target regardless of what port-scanning could confirm - fall back
        # to scanning it directly via its own scheme instead of giving up.
        if target_ip.startswith("https://"):
            web_port = 443
            logger.warning("[Scanner Node] No confirmed port from recon; falling back to scheme-inferred port 443 for %s", target_ip)
        elif target_ip.startswith("http://"):
            web_port = 80
            logger.warning("[Scanner Node] No confirmed port from recon; falling back to scheme-inferred port 80 for %s", target_ip)

        if web_port:
            # exploit_node independently re-derives its web port from
            # state["open_ports"] - persist the fallback here too, or
            # exploit would redundantly fail with "no web-capable port"
            # right after scanner just successfully used this same port.
            state["open_ports"] = [web_port]

    if not web_port:
        state["current_payload"] = None
        state["vulnerabilities"] = []
        state["last_error"] = state.get("last_error") or "No web-capable port available for scanning"
        record_state_event(state, "scanner", "failed", "No web-capable port available for scanning")
        return state

    target_url = _build_target_url(state["target_ip"], web_port)
    findings = []
    scan_outputs = {}

    try:
        tools = WSLBridgeTools()
        nikto_report = tools.run_nikto(target_url)
        ffuf_report = tools.run_ffuf_discovery(target_url)
        scan_outputs = {"nikto": nikto_report, "ffuf": ffuf_report, "target_url": target_url, "port": web_port}

        if nikto_report:
            for line in nikto_report.splitlines():
                if line.strip().startswith("+"):
                    findings.append({"tool": "nikto", "port": web_port, "summary": line.strip(), "url": target_url})

        if ffuf_report and "No notable paths" not in ffuf_report:
            findings.append({"tool": "ffuf", "port": web_port, "summary": ffuf_report.splitlines()[0], "url": target_url})

    except Exception as e:
        logger.error("[Scanner Node] Scan execution failed: %s", e)
        state["error_log"].append(f"Scanner failed: {e}")
        state["last_error"] = str(e)
        scan_outputs = {"error": str(e), "target_url": target_url, "port": web_port}

    state["extracted_data"]["scanner"] = scan_outputs
    state["vulnerabilities"] = findings

    if findings:
        vuln_text = " ".join(f.get("summary", "") for f in findings).lower()
        if "sql" in vuln_text:
            state["current_payload"] = "sqli"
        elif any(term in vuln_text for term in ["traversal", "lfi", "file inclusion"]):
            state["current_payload"] = "path_traversal"
        else:
            state["current_payload"] = "generic_probe"
        state["progress_pct"] = max(state.get("progress_pct", 25), 55)
        record_state_event(state, "scanner", "completed", f"Scanner found {len(findings)} finding(s) on {target_url}")
    else:
        state["current_payload"] = "generic_probe"
        state["progress_pct"] = max(state.get("progress_pct", 25), 50)
        record_state_event(state, "scanner", "completed", f"Scanner completed on {target_url} with no confirmed findings")

    return state
