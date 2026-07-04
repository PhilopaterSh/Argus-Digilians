import logging
from urllib.parse import urlparse

from app.core.agent.contracts import record_state_event, utc_now_iso
from app.core.agent.state import AgentState
from app.tools.tool_registry import WSLBridgeTools

logger = logging.getLogger(__name__)


def _first_web_port(open_ports):
    for port in open_ports:
        if port in {80, 443, 8080, 8000, 8443}:
            return port
    return open_ports[0] if open_ports else None


def _build_target_url(target: str, port: int) -> str:
    parsed = urlparse(target if target.startswith("http") else f"http://{target}")
    host = parsed.netloc or parsed.path
    scheme = "https" if port in {443, 8443} else "http"
    return f"{scheme}://{host}:{port}" if ":" not in host else f"{scheme}://{host}"


def scanner_node(state: AgentState) -> AgentState:
    logger.info("[Scanner Node] Analyzing open ports for vulnerabilities...")
    record_state_event(state, "scanner", "running", "Starting vulnerability scanning")
    state["current_node"] = "scanner"
    state["status"] = "running"
    state["updated_at"] = utc_now_iso()

    web_port = _first_web_port(state.get("open_ports", []))
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
