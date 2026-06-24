import streamlit as st
import threading
import time
import os
import sys
import traceback
from dotenv import load_dotenv

# Ensure project root is importable
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from app.tools.tool_registry import WSLBridgeTools
# ArgusBrain may live in app.core.brain or legacy core.agent
try:
    from app.core.brain import ArgusBrain
except Exception:
    try:
        from core.agent import ArgusBrain
    except Exception:
        ArgusBrain = None

load_dotenv()

st.set_page_config(page_title="Argus AI - Studio (Streamlit)", page_icon="🛡️", layout="wide")

st.title("Argus AI Security Studio")

# Sidebar: inputs and controls
with st.sidebar:
    st.header("Controls")
    target = st.text_input("Target URL", value="https://example.com")
    temperature = st.slider("AI Temperature", 0.0, 1.0, 0.2)
    run_btn = st.button("Start Scan")
    stop_btn = st.button("Stop Scan")
    st.markdown("---")
    st.write("Model:")
    model_name = st.text_input("Model Name", value=os.getenv("SELECTED_MODEL", "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"))

# Initialize bridge and brain singletons in session_state
if 'bridge' not in st.session_state:
    st.session_state.bridge = WSLBridgeTools()
if 'brain' not in st.session_state:
    if ArgusBrain is not None:
        st.session_state.brain = ArgusBrain(model_name, [])
    else:
        st.session_state.brain = None

bridge = st.session_state.bridge
brain = st.session_state.brain

# Layout: two columns
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Agent Mind")
    status_placeholder = st.empty()
    thoughts_box = st.empty()
    output_box = st.empty()
    download_placeholder = st.empty()

with col_right:
    st.subheader("Blackboard & Findings")
    findings_box = st.empty()
    last_run_box = st.empty()

# Run control state
if 'running' not in st.session_state:
    st.session_state.running = False
if 'last_report' not in st.session_state:
    st.session_state.last_report = None
if 'last_results' not in st.session_state:
    st.session_state.last_results = None
if 'thread_exc' not in st.session_state:
    st.session_state.thread_exc = None
if 'scan_log' not in st.session_state:
    st.session_state.scan_log = []

# Background task
def run_scan(target_url, model_name, temperature):
    try:
        st.session_state.running = True
        st.session_state.scan_log.append(f"Starting recon for: {target_url}")
        status_placeholder.info(f"Starting recon for: {target_url}")
        st.session_state.scan_log.append("Initializing WSL recon suite...")

        # 1. quick reachability
        reach = bridge.check_reachability(target_url)
        st.session_state.scan_log.append(f"Reachability:\n{reach}")

        # 2. full recon (this runs in WSL and may take time)
        st.session_state.scan_log.append("Running full recon suite (this may take a while)...")
        report_display = bridge.recon_suite(target_url)
        st.session_state.last_results = bridge.last_recon_results
        st.session_state.scan_log.append("Recon report ready.")

        # 3. prepare AI input
        results = st.session_state.last_results or {}
        if isinstance(results, dict) and results.get('ai_input'):
            report_for_ai = results.get('ai_input')
            st.session_state.scan_log.append("Using explicit ai_input from recon results.")
        else:
            parts = []
            for k in ('tech','ports','dns'):
                v = results.get(k) if isinstance(results, dict) else None
                if v:
                    parts.append(f"[{k}] {v[:800]}")
            report_for_ai = "\n\n".join(parts) if parts else report_display
            if len(report_for_ai) > 3000:
                report_for_ai = report_for_ai[:3000] + "\n...[truncated]"
            st.session_state.scan_log.append("Prepared condensed AI input from recon fields.")

        # 4. call AI analysis if available
        if brain is not None:
            st.session_state.scan_log.append("Sending condensed report to AI for analysis...")
            try:
                analysis = brain.ask(f"Analyze reconnaissance report for {target_url}. Context: {report_for_ai}")
                ai_output = analysis.get('output') if isinstance(analysis, dict) else str(analysis)
                st.session_state.scan_log.append("AI analysis complete.")
            except Exception as e:
                ai_output = f"AI analysis failed: {e}"
                st.session_state.scan_log.append(ai_output)
        else:
            ai_output = "AI engine not available in this environment."
            st.session_state.scan_log.append(ai_output)

        # Save last report
        full_export = f"# Argus Security Report - {target_url}\n\n## Technical Data\n{report_display}\n\n## AI Analysis\n{ai_output}"
        st.session_state.last_report = full_export
        st.session_state.running = False
        status_placeholder.success("Scan complete")
        st.session_state.scan_log.append("Scan complete")
        st.session_state.scan_log.append("\n--- AI Output ---\n" + (ai_output or ''))
        st.session_state.scan_log.append("\n--- Raw Recon ---\n" + (report_display or ''))
        last_run_box.info(f"Last run: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as exc:
        st.session_state.thread_exc = traceback.format_exc()
        st.session_state.running = False
        status_placeholder.error("Scan failed: see exception")
        st.session_state.scan_log.append("Exception:\n" + st.session_state.thread_exc)

# Auto-refresh while running so UI updates
if st.session_state.running:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=1000, key='autorefresh')
    except Exception:
        # If streamlit_autorefresh not available, fall back to experimental rerun
        st.experimental_rerun()

# Render live log
log_text = "\n".join(st.session_state.scan_log[-200:]) if st.session_state.scan_log else "No logs yet."
# render in the thoughts_box with preserved terminal styling
thoughts_box.markdown(f"<div class=\"terminal-box\">{log_text.replace('\n','<br/>')}</div>", unsafe_allow_html=True)

# Show any thread exception
if st.session_state.thread_exc:
    st.error("Background task exception:")
    st.code(st.session_state.thread_exc)

# Handle stop
if stop_btn and st.session_state.running:
    # We don't have a clean cancellation token for WSL calls; set flag and inform user
    st.session_state.running = False
    status_placeholder.warning("Stop requested. Long-running WSL processes may still complete in background.")

# Trigger run
if run_btn and not st.session_state.running:
    t = threading.Thread(target=run_scan, args=(target, model_name, temperature), daemon=True)
    t.start()
    status_placeholder.info("Scan started in background...")

# Download report button if available
if st.session_state.last_report:
    download_placeholder.download_button(label="Download Last Report", data=st.session_state.last_report, file_name=f"Argus_Report_{int(time.time())}.md", mime='text/markdown')

# Show any thread exception
if st.session_state.thread_exc:
    st.error("Background task exception:")
    st.code(st.session_state.thread_exc)

# Monitor external CLI progress
st.markdown("---")
with st.expander("Monitor CLI progress (follow a target run by LAUNCH_CLI)"):
    monitor_target = st.text_input("Monitor Target URL (exact)", key="monitor_target_input")
    if st.button("Start Monitoring", key="start_monitor"):
        st.session_state.monitor_target = monitor_target
    if st.button("Stop Monitoring", key="stop_monitor"):
        st.session_state.monitor_target = None

    mon_tgt = st.session_state.get('monitor_target')
    if mon_tgt:
        # locate progress file
        import pathlib
        safe = ''.join(c for c in mon_tgt if c.isalnum() or c in '-_.').rstrip()
        safe = safe.replace('https://','').replace('http://','').replace('/','_')
        path = pathlib.Path('reports') / f"{safe}_progress.log"
        if path.exists():
            content = path.read_text(encoding='utf-8')
            st.markdown(f"**Monitoring:** {mon_tgt}")
            st.markdown(f"<div class=\"terminal-box\">{content.replace('\n','<br/>')}</div>", unsafe_allow_html=True)
        else:
            st.info(f"No progress file found yet for {mon_tgt}. It will appear once LAUNCH_CLI writes progress to reports/.")

# Small status footer
st.markdown("---")
st.caption(f"WSL Bridge: {bridge.host} | Model: {model_name} | Running: {st.session_state.running}")

# Suggestion for users
st.info("Tip: Use the sidebar to adjust AI parameters. For heavy scans, run in a controlled manner.")
