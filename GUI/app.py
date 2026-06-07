import streamlit as st
import sys
import os

# Ensure project root is in path for core module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tools import WSLBridgeTools
from core.agent import ArgusBrain
from langchain_core.tools import Tool
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

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

def load_brain(model_name):
    tools = [
        Tool(name="Check_Reachability", func=bridge.check_reachability, description="Verify if the target domain is reachable before scanning."),
        Tool(name="Subdomain_Enumeration", func=bridge.enumerate_subdomains, description="Discover subdomains to map the target's attack surface."),
        Tool(name="Recon_Suite", func=bridge.recon_suite, description="Execute parallel advanced recon (WAF, Nmap, WhatWeb, HTTP Headers, Spider) inside Kali."),
        Tool(name="Query_Memory", func=bridge.get_intelligence_summary, description="Query the internal Shared Memory (Blackboard) for a summary of all findings."),
        Tool(name="Query_Knowledge_Graph", func=bridge.query_knowledge_graph, description="Access the Knowledge Graph to find cross-target relationships, shared infrastructure, and lateral movement paths."),
        Tool(name="Exploit_Suggester", func=bridge.suggest_payloads, description="Search PayloadsAllTheThings for test payloads."),
        Tool(name="Smart_Web_Search", func=bridge.smart_web_search, description="Search internet for CVEs/Exploits/Security info."),
        Tool(name="Run_Nikto", func=bridge.run_nikto, description="Run Nikto vulnerability scanner against a web target."),
        Tool(name="Run_FFUF", func=bridge.run_ffuf_discovery, description="Run FFUF for fast hidden path discovery.")
    ]
    return ArgusBrain(model_name, tools)

# Main Interface
target = st.text_input("🎯 Target URL", "https://")

if st.button("RUN ANALYSIS"):
    if target:
        brain = load_brain(model)
        
        with st.status("🕵️ Argus Agent is thinking...", expanded=True) as status:
            try:
                st.write("Initializing autonomous security reasoning...")
                st_callback = StreamlitCallbackHandler(st.container())
                
                # The Agent now takes full control and shows its thoughts live in the UI
                analysis = brain.ask(
                    f"Perform a comprehensive security analysis for {target}. Start with reachability, then map the attack surface, and finally provide a deep risk assessment.",
                    callbacks=[st_callback]
                )
                
                st.markdown("### 📋 Final Security Report")
                st.info(analysis["output"])
                
                status.update(label="Analysis Finished!", state="complete")
                
                # --- Export Feature ---
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=analysis["output"],
                    file_name=f"Argus_Report_{target.replace('https://', '').replace('http://', '').replace('/', '_')}.md",
                    mime="text/markdown"
                )
            except Exception as e:
                st.error(f"❌ Critical Error during AI Analysis: {str(e)}")
                st.warning("🔄 Suggestion: Restart Argus and try 'Force CPU Mode' if this is a GPU/CUDA error.")
                status.update(label="Analysis Failed", state="error")
