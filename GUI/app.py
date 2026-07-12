"""
Argus AI Studio - Unified Streamlit GUI v2.0
Single-mode: all 13 pipeline steps + full port scan + FFUF enabled.
"""
import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv()

from core.tools import WSLBridgeTools
from core.agent_ai_driven import ArgusBrain   # AI-driven brain (LLM decides each step)
from core.memory import ArgusMemory
from core.safety import SafetyLayer
from langchain_core.tools import Tool

# Palette:
#   Background : #d1dbe4  (steel blue-gray)
#   Accent     : #194a7a  (deep navy)

# ── PAGE CONFIG ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Argus AI Security Studio",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLING ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── App background ── */
.stApp {
    background: #d1dbe4;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #eaf0f5;
    border-right: 1px solid #a8bfce;
}

/* ── Header card ── */
.main-header {
    text-align: center;
    padding: 2rem;
    background: #ffffff;
    border-radius: 15px;
    border: 1px solid #194a7a;
    box-shadow: 0 2px 16px rgba(25,74,122,0.12);
    margin-bottom: 2rem;
}
.main-header h1 {
    color: #194a7a;
    letter-spacing: 3px;
    font-size: 2rem;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 0;
}
.main-header .divider {
    height: 3px;
    width: 80px;
    background: #194a7a;
    border-radius: 2px;
    margin: 0.6rem auto 0.8rem;
}
.main-header p {
    color: #4a6880;
    margin: 0;
}

/* ── Terminal / log box ── */
.terminal-box {
    background: #0d1b2a;
    color: #a8d8f0;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #194a7a;
    font-family: 'Courier New', monospace;
    white-space: pre-wrap;
    font-size: 0.8rem;
    max-height: 500px;
    overflow-y: auto;
}

/* ── Metric card ── */
.metric-card {
    background: #ffffff;
    border: 1px solid #194a7a;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
}

/* ── Buttons ── */
.stButton>button {
    background: linear-gradient(135deg, #194a7a, #123a61) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
    width: 100%;
    transition: all 0.25s ease;
    letter-spacing: 0.5px;
}
.stButton>button:hover {
    box-shadow: 0 4px 18px rgba(25,74,122,0.45) !important;
    transform: translateY(-1px);
}

/* ── Active tab ── */
button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid #194a7a !important;
    color: #194a7a !important;
    font-weight: 600;
}

/* ── Severity badges ── */
.severity-critical { color: #DC2626; font-weight: 700; }
.severity-high     { color: #EA580C; font-weight: 700; }
.severity-medium   { color: #D97706; }
.severity-low      { color: #194a7a; }
.severity-info     { color: #4a6880; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ──────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>ARGUS AI Security Studio</h1>
    <div class="divider"></div>
    <p>Autonomous Intelligence and Reconnaissance Framework v2.0</p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ─────────────────────────────────────────────────────
SCAN_MODE = "aggressive"   # unified mode — all features enabled

with st.sidebar:
    st.markdown("### Configuration")
    model = os.getenv("SELECTED_MODEL", "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest")
    st.info(f"AI Model: {model.split('/')[-1]}")

    st.markdown("---")
    st.markdown("### System Status")
    memory = ArgusMemory()
    st.metric("Past Scans", len(memory.get_scan_history(limit=1000)))

    st.markdown("---")
    st.markdown("### Safety Layer")
    safety = SafetyLayer()
    st.success("Safety Layer: ACTIVE")

    st.markdown("---")
    if st.button("Clear Memory DB"):
        memory.clear_memory()
        st.warning("Memory cleared.")

# ── BRIDGE / BRAIN FACTORY ───────────────────────────────────────
def get_bridge():
    return WSLBridgeTools(scan_mode=SCAN_MODE)

def get_brain(bridge, model_name):
    tools = [
        Tool(name="Check_Reachability",    func=bridge.check_reachability,
             description="Verify if the target domain is reachable."),
        Tool(name="Subdomain_Enumeration", func=bridge.enumerate_subdomains,
             description="Discover subdomains to map the attack surface."),
        Tool(name="Get_Priority_Targets",  func=bridge.get_priority_targets,
             description="Get ranked list of discovered subdomains from memory."),
        Tool(name="Recon_Suite",           func=bridge.recon_suite,
             description="Execute parallel recon: WAF, Nmap, WhatWeb, Headers, Fuzzing."),
        Tool(name="Run_Nikto",             func=bridge.run_nikto,
             description="Run Nikto web vulnerability scanner."),
        Tool(name="Smart_Web_Search",      func=bridge.smart_web_search,
             description="Search the web for CVEs, exploits, and tech info."),
        Tool(name="Query_Scenario_KB",     func=bridge.retrieve_similar_scenarios,
             description="Semantic RAG lookup over 1,040 labeled test scenarios: what Argus "
                         "typically catches/misses for a given tech/target description."),
        Tool(name="Query_Memory",          func=bridge.get_intelligence_summary,
             description="Get consolidated intelligence from the Blackboard."),
        Tool(name="Query_Knowledge_Graph", func=bridge.query_knowledge_graph,
             description="Find cross-target relationships in the Knowledge Graph."),
        Tool(name="Exploit_Suggester",     func=bridge.suggest_payloads,
             description="Get relevant test payloads from PayloadsAllTheThings."),
        Tool(name="Generate_Report",       func=bridge.generate_report,
             description="Generate final JSON and Markdown security report."),
        Tool(name="Path_Traversal_Check",  func=bridge.check_path_traversal,
             description="Test for path traversal / LFI vulnerabilities."),
        Tool(name="XSS_Check",             func=bridge.check_xss,
             description="Test for reflected XSS vulnerabilities."),
        Tool(name="SQLi_Check",            func=bridge.check_sqli,
             description="Test for SQL injection vulnerabilities."),
    ]
    return ArgusBrain(model_name, tools)


def _render_result(result: dict, target_url: str):
    """Render a finished (or partial) scan result. No DB writes here."""
    output_str = result.get("output_str", str(result.get("output", "")))
    if result.get("stopped"):
        st.warning("Scan was STOPPED early by the user — this is a PARTIAL report.")

    st.markdown("### Final Security Report")
    report_data = result.get("report_data", {})
    _sev_label = {"Critical": "[CRITICAL]", "High": "[HIGH]",
                  "Medium": "[MEDIUM]", "Low": "[LOW]", "Info": "[INFO]"}
    if report_data:
        meta     = report_data.get("meta", {})
        findings = report_data.get("findings", [])
        summary  = report_data.get("summary", {})
        col_r, col_f = st.columns(2)
        col_r.metric("Risk Score", f"{meta.get('risk_score', 0)}/10")
        col_f.metric("Findings",   len(findings))
        for sev, cnt in summary.get("severity_breakdown", {}).items():
            if cnt:
                st.write(f"{_sev_label.get(sev, '[INFO]')} **{sev}:** {cnt}")
        if findings:
            st.markdown("---\n**Findings:**")
            for f in findings:
                sev = f.get("severity", "Info")
                st.markdown(
                    f"{_sev_label.get(sev, '[INFO]')} **[{sev}]** `{f.get('target','')}` "
                    f"— {f.get('summary','')}"
                )

    with st.expander("Pipeline Log", expanded=not bool(report_data)):
        # Render as preformatted text (NOT markdown) so bare URLs like
        # www.example.com are not auto-converted into clickable links, and the
        # phase/box-drawing layout is preserved verbatim.
        st.code(output_str, language="text")

    st.download_button(
        label="Download Markdown Report",
        data=output_str,
        file_name=f"Argus_{target_url.replace('https://', '').replace('/', '_')}.md",
        mime="text/markdown",
        key=f"dl_{target_url}",
    )


# ── TABS ─────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Analysis", "Scan History"])

# ── TAB 1: ANALYSIS ──────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Target")
        target_url = st.text_input(
            "Target / Pattern",
            "https://example.com",
            help=(
                "Supported patterns:\n"
                "  example.com          — full vulnerability scan (all 13 steps)\n"
                "  *.example.com        — subdomain enumeration only\n"
                "  example.com/*/*/*    — directory/path enumeration (depth = wildcard count)\n"
                "  *.example.com/*/*/*  — subdomain + directory enumeration"
            )
        )
        # ── Scan state (survives Streamlit reruns) ────────────────────────
        ss = st.session_state
        ss.setdefault("scan_running", False)
        ss.setdefault("scan_box", None)
        ss.setdefault("scan_cancel", None)
        ss.setdefault("scan_started", None)
        ss.setdefault("scan_target", None)

        b_run, b_stop = st.columns(2)
        run_btn = b_run.button("EXECUTE ANALYSIS", key="run_analysis",
                               disabled=ss.scan_running, use_container_width=True)
        stop_btn = b_stop.button("■ STOP TESTING", key="stop_analysis",
                                 disabled=not ss.scan_running, use_container_width=True)

        # Handle STOP: signal the running scan to cancel cooperatively.
        if stop_btn and ss.scan_running and ss.scan_cancel is not None:
            ss.scan_cancel.set()
            st.warning("Stopping… Argus will finish the current tool, then produce a partial report.")

        st.markdown("---")

        # ── Dynamic mode badge ────────────────────────────────────────────────
        _raw = (target_url or "").strip()
        _sub  = _raw.startswith("*.")
        _dir  = "/*" in _raw
        if _sub and _dir:
            _label = "SUBDOMAIN + DIRECTORY ENUM"
            _bg    = "#5b3fa0"
        elif _sub:
            _label = "SUBDOMAIN ENUMERATION"
            _bg    = "#194a7a"
        elif _dir:
            _d     = _raw.count("/*")
            _label = f"DIRECTORY ENUM  (depth {_d})"
            _bg    = "#0d6e47"
        else:
            _label = "FULL SCAN  |  ALL MODULES ACTIVE"
            _bg    = "#194a7a"

        st.markdown(
            f"<div style='background:{_bg};color:#fff;border-radius:6px;"
            f"padding:6px 12px;font-size:0.8rem;font-weight:600;letter-spacing:1px;'>"
            f"{_label}</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.subheader("Intelligence Output")

        # 1) START — launch the scan in a background thread so STOP stays clickable.
        if run_btn:
            if not target_url or target_url.strip() in ("", "https://"):
                st.warning("Please enter a valid target URL.")
            else:
                safety_check = SafetyLayer()
                is_valid, reason = safety_check.validate_target(target_url, SCAN_MODE)
                if not is_valid:
                    st.error(f"Safety Block: {reason}")
                else:
                    import threading
                    ev  = threading.Event()
                    box = {"result": None, "error": None, "done": False}
                    q      = target_url.strip()
                    _model = model

                    def _worker():
                        # Build the bridge/brain INSIDE the thread so every SQLite
                        # connection is created in this thread (no cross-thread reuse).
                        try:
                            _bridge = get_bridge()
                            _brain  = get_brain(_bridge, _model)
                            box["result"] = _brain.ask(q, cancel_event=ev)
                        except Exception as _e:
                            box["error"] = str(_e)
                        finally:
                            box["done"] = True

                    th = threading.Thread(target=_worker, daemon=True)
                    ss.scan_running = True
                    ss.scan_cancel  = ev
                    ss.scan_box     = box
                    ss.scan_started = datetime.now().isoformat()
                    ss.scan_target  = q
                    ss.scan_logged  = False
                    th.start()
                    st.rerun()

        # 2) POLL — a scan is in progress; refresh until the worker thread finishes.
        if ss.scan_running:
            box = ss.scan_box or {}
            if box.get("done"):
                ss.scan_running = False
                if box.get("error"):
                    st.error(f"Error: {box['error']}")
                    st.info("Tip: Ensure Ollama is running and WSL Kali is active.")
                else:
                    result = box.get("result", {}) or {}
                    if not ss.get("scan_logged"):
                        try:
                            memory.log_scan_session(
                                target=ss.scan_target, mode=SCAN_MODE,
                                started_at=ss.scan_started,
                                completed_at=datetime.now().isoformat(),
                                findings_count=result.get("findings_count", 0),
                                risk_score=result.get("risk_score", 0),
                                report_path=result.get("md_path", ""),
                            )
                        except Exception:
                            pass
                        ss.scan_logged = True
                    _render_result(result, ss.scan_target)
            else:
                import time as _time
                st.info(f"Argus is analyzing **{ss.scan_target}** …  "
                        f"press **■ STOP TESTING** to cancel.")
                st.caption("Running security modules — this can take a few minutes.")
                _time.sleep(1.5)
                st.rerun()

        # 3) IDLE — show the most recent finished scan (survives reruns).
        elif ss.scan_box and ss.scan_box.get("done") and not ss.scan_box.get("error"):
            _render_result(ss.scan_box.get("result", {}) or {}, ss.scan_target)

# ── TAB 2: SCAN HISTORY ──────────────────────────────────────────
with tab2:
    st.subheader("Scan History Dashboard")
    history = memory.get_scan_history(limit=100)

    if not history:
        st.info("No scans recorded yet. Run an analysis to see history here.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Scans",    len(history))
        avg_score = sum(s.get("risk_score", 0) for s in history) / len(history)
        m2.metric("Avg Risk Score", f"{avg_score:.1f}/10")
        total_findings = sum(s.get("findings", 0) for s in history)
        m3.metric("Total Findings", total_findings)
        all_cves = sum(1 for s in history if s.get("risk_score", 0) >= 7)
        m4.metric("High-Risk Scans", all_cves)

        st.markdown("---")
        st.markdown("**Recent Scans:**")
        for scan in history:
            risk = scan.get("risk_score", 0)
            with st.expander(
                f"{scan.get('target', 'Unknown')} | Risk: {risk}/10 | "
                f"{scan.get('started', '')}"
            ):
                st.markdown(f"- **Findings:** {scan.get('findings', 0)}")
                st.markdown(f"- **Started:** {scan.get('started', 'N/A')}")
                st.markdown(f"- **Completed:** {scan.get('completed', 'N/A')}")
                rpt = scan.get("report", "")
                if rpt:
                    st.markdown(f"- **Report:** `{rpt}`")
                    import os as _os
                    # Download Markdown report
                    if _os.path.isfile(rpt):
                        with open(rpt, 'r', encoding='utf-8', errors='replace') as _f:
                            _md_content = _f.read()
                        _safe_name = scan.get('target', 'report').replace('https://', '').replace('/', '_')
                        st.download_button(
                            label="Download Markdown Report",
                            data=_md_content,
                            file_name=f"argus_{_safe_name}.md",
                            mime="text/markdown",
                            key=f"dl_md_{scan.get('started', '')}_{scan.get('target', '')}"
                        )
                    # Download JSON report (same directory, .json extension)
                    _json_path = rpt.replace('.md', '.json') if rpt.endswith('.md') else rpt + '.json'
                    if _os.path.isfile(_json_path):
                        with open(_json_path, 'r', encoding='utf-8', errors='replace') as _f:
                            _json_content = _f.read()
                        st.download_button(
                            label="Download JSON Report",
                            data=_json_content,
                            file_name=f"argus_{_safe_name}.json",
                            mime="application/json",
                            key=f"dl_json_{scan.get('started', '')}_{scan.get('target', '')}"
                        )
                else:
                    st.info("No report saved for this scan. Run the scan again to generate one.")

        st.markdown("---")
        st.subheader("Intelligence Blackboard")
        bb = memory.get_blackboard_summary()
        st.markdown(f'<div class="terminal-box">{bb}</div>', unsafe_allow_html=True)

        st.subheader("Knowledge Graph")
        kg = memory.get_graph_insights()
        st.markdown(f'<div class="terminal-box">{kg}</div>', unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────
st.markdown("""
<div style="position:fixed; bottom:10px; right:16px; color:#4a6880;
            font-size:0.72rem; letter-spacing:0.4px;">
    <span style="color:#194a7a; font-weight:600;">ARGUS</span>
    v2.0 &nbsp;|&nbsp; Authorized Security Testing Only
</div>
""", unsafe_allow_html=True)
