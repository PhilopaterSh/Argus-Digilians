import streamlit as st
import os
import sys
import time
from dotenv import load_dotenv

# Ensure project root is in path for core module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tools.tool_registry import WSLBridgeTools
try:
    from app.core.brain import ArgusBrain
except Exception:
    try:
        # Legacy location fallback
        from core.agent import ArgusBrain
    except Exception:
        ArgusBrain = None
from langchain_core.tools import Tool

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Argus AI - Security Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced Custom CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'JetBrains+Mono', monospace;
    }

    .main {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #00ff41;
    }
    
    .stApp {
        background-color: transparent;
    }

    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: rgba(0, 0, 0, 0.6);
        border-radius: 15px;
        border: 1px solid #00ff41;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.2);
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #00ff41;
        text-transform: uppercase;
        letter-spacing: 5px;
        margin: 0;
    }

    /* Terminal Style Recon Box */
    .terminal-box {
        background-color: #000000;
        color: #00ff41;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #333;
        font-family: 'JetBrains+Mono', monospace;
        margin-top: 10px;
        white-space: pre-wrap;
        font-size: 0.85rem;
        border-left: 4px solid #00ff41;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #00ff41 !important;
        color: black !important;
        font-weight: bold !important;
        border-radius: 5px !important;
        border: none !important;
        transition: 0.3s !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: #008f11 !important;
        box-shadow: 0 0 15px #00ff41 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Custom Header ---
st.markdown("""
    <div class="main-header">
        <h1>Argus AI Security Studio</h1>
        <p style="color: #888;">Autonomous Intelligence & Reconnaissance Framework v1.0</p>
    </div>
    """, unsafe_allow_html=True)

# --- Initialization ---
bridge = WSLBridgeTools()
MODEL_NAME = os.getenv("SELECTED_MODEL", "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest")

@st.cache_resource
def get_brain():
    tools = [
        Tool(name="Check_Reachability", func=bridge.check_reachability, description="Verify target via WSL network."),
        Tool(name="Subdomain_Enumeration", func=bridge.enumerate_subdomains, description="Fast subdomain discovery."),
        Tool(name="Recon_Suite", func=bridge.recon_suite, description="Execute multi-tool parallel recon in WSL Kali.")
    ]
    return ArgusBrain(MODEL_NAME, tools)

# --- UI Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("System Status")
    st.success(f"WSL Bridge: ACTIVE ({bridge.host})")
    st.info(f"AI Engine: {MODEL_NAME}")
    
    st.markdown("---")
    url_input = st.text_input("Target URL", "https://example.com")
    run_btn = st.button("EXECUTE ANALYSIS")

with col2:
    st.subheader("Intelligence Output")
    if run_btn:
        if url_input:
            brain = get_brain()
            with st.status("📡 Bridging to WSL Kali...", expanded=True) as status:
                st.write("Initializing Parallel Recon Subsystem...")
                # recon_suite returns the full string for display
                report_display = bridge.recon_suite(url_input)
                results = bridge.last_recon_results
                report_for_ai = results["ai_input"]
                
                st.markdown("#### Technical Evidence:")
                st.markdown(f'<div class="terminal-box">{report_display}</div>', unsafe_allow_html=True)
                
                st.write("🧠 AI Analyzing technical data...")
                # We use the condensed summary for the AI to improve precision and save context
                analysis = brain.ask(f"Analyze this reconnaissance report from WSL for {url_input}. Focus on risks and vulnerabilities based on this summary: {report_for_ai}")
                
                st.markdown("#### AI Intelligence Report:")
                st.info(analysis["output"])
                
                status.update(label="Analysis Complete!", state="complete")
                
                # Report Export
                full_export = f"# Argus Security Report - {url_input}\n\n## Technical Data\n{report_display}\n\n## AI Analysis\n{analysis['output']}"
                st.download_button(
                    label="📥 DOWNLOAD MARKDOWN REPORT",
                    data=full_export,
                    file_name=f"Argus_{url_input.replace('https://', '').replace('/', '_')}.md",
                    mime="text/markdown"
                )
        else:
            st.warning("Please enter a valid target URL.")

st.markdown("""
    <div style="position: fixed; bottom: 10px; right: 10px; color: #555; font-size: 0.8rem;">
        Argus Framework v1.0 | Security Intelligence Division
    </div>
    """, unsafe_allow_html=True)
