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

# Background task
def run_scan(target_url, model_name, temperature):
    try:
        st.session_state.running = True
        status_placeholder.info(f"Starting recon for: {target_url}")
        thoughts_box.code("Initializing WSL recon suite...\n")
        # 1. quick reachability
        reach = bridge.check_reachability(target_url)
        thoughts_box.code(f"Reachability check:\n{reach}\n", language='text')

        # 2. full recon (this runs in WSL and may take time)
        report_display = bridge.recon_suite(target_url)
        st.session_state.last_results = bridge.last_recon_results
        thoughts_box.code(f"Recon report ready.\n", language='text')

        # 3. prepare AI input
        results = st.session_state.last_results or {}
        if isinstance(results, dict) and results.get('ai_input'):
            report_for_ai = results.get('ai_input')
        else:
            parts = []
            for k in ('tech','ports','dns'):
                v = results.get(k) if isinstance(results, dict) else None
                if v:
                    parts.append(f"[{k}] {v[:800]}")
            report_for_ai = "\n\n".join(parts) if parts else report_display
            if len(report_for_ai) > 3000:
                report_for_ai = report_for_ai[:3000] + "\n...[truncated]"

        # 4. call AI analysis if available
        if brain is not None:
            thoughts_box.code("Sending condensed report to AI for analysis...\n")
            try:
                analysis = brain.ask(f"Analyze reconnaissance report for {target_url}. Context: {report_for_ai}")
                ai_output = analysis.get('output') if isinstance(analysis, dict) else str(analysis)
            except Exception as e:
                ai_output = f"AI analysis failed: {e}"
        else:
            ai_output = "AI engine not available in this environment."

        # Save last report
        full_export = f"# Argus Security Report - {target_url}\n\n## Technical Data\n{report_display}\n\n## AI Analysis\n{ai_output}"
        st.session_state.last_report = full_export
        st.session_state.running = False
        status_placeholder.success("Scan complete")
        output_box.code(ai_output)
        findings_box.text(report_display)
        last_run_box.info(f"Last run: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as exc:
        st.session_state.thread_exc = traceback.format_exc()
        st.session_state.running = False
        status_placeholder.error("Scan failed: see exception")
        output_box.code(st.session_state.thread_exc)

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

# Small status footer
st.markdown("---")
st.caption(f"WSL Bridge: {bridge.host} | Model: {model_name} | Running: {st.session_state.running}")

# Suggestion for users
st.info("Tip: Use the sidebar to adjust AI parameters. For heavy scans, run in a controlled manner.")
