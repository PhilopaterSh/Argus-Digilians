import streamlit as st
import sys
import os

# Ensure project root is in path for core module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tools import WSLBridgeTools
from core.agent import ArgusBrain
from langchain_core.tools import Tool

# --- UI Setup ---
st.set_page_config(page_title="Argus AI Studio - WSL Bridge", layout="wide")

# تصميم بسيط واحترافي
st.markdown("""
    <style>
    .report-card {
        background-color: #111;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00ff41;
        font-family: monospace;
        color: #00ff41;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Argus AI Studio (WSL Bridge)")

# Sidebar
with st.sidebar:
    st.header("⚙️ Bridge Configuration")
    st.info("App: Docker Container")
    st.info("Tools: Local WSL Kali")
    # Only use WhiteRabbitNeo as requested
    model = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"
    st.write(f"**Intelligence Model:** {model}")
    
    st.markdown("---")
    st.subheader("SSH Credentials")
    wsl_user = st.text_input("WSL User", os.getenv("WSL_USER", "kali"))
    wsl_pass = st.text_input("WSL Pass", os.getenv("WSL_PASS", "kali"), type="password")

# Logic Initialization
# Pass dynamic credentials if needed, or rely on ENV
bridge = WSLBridgeTools()

@st.cache_resource
def load_brain(model_name):
    tools = [
        Tool(name="Check_Reachability", func=bridge.check_reachability, description="Verify target via WSL network."),
        Tool(name="Recon_Suite", func=bridge.recon_suite, description="Execute WhatWeb and HTTPX inside WSL Kali.")
    ]
    return ArgusBrain(model_name, tools)

# Main Interface
target = st.text_input("🎯 Target URL", "https://")

if st.button("RUN ANALYSIS"):
    if target:
        brain = load_brain(model)
        
        with st.status("🕵️ Bridging to WSL Kali...", expanded=True) as status:
            st.write("Executing remote reconnaissance...")
            report = bridge.recon_suite(target)
            
            st.markdown("### 📋 Evidence from WSL")
            st.markdown(f"<div class='report-card'>{report.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
            
            st.write("AI Analysis in progress...")
            analysis = brain.ask(f"Analyze this reconnaissance report from WSL for {target}. Report: {report}")
            
            st.markdown("### 🧠 AI Intelligence Report")
            st.info(analysis["output"])
            
            status.update(label="Analysis Finished!", state="complete")
