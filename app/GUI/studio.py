import streamlit as st
import sys
import os
import concurrent.futures
import re
from typing import Optional

# Ensure project root is in path for module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.tools.tool_registry import WSLBridgeTools
from app.core.brain import ArgusBrain
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
        Tool(name="Run_FFUF", func=bridge.run_ffuf_discovery, description="Run FFUF for fast hidden path discovery."),
        Tool(name="System_Self_Heal", func=bridge.system_self_heal, description="Use this tool to autonomously install missing Python libraries (pip) or Kali system tools (apt) if you encounter a 'command not found' or 'ModuleNotFoundError'."),
        Tool(name="Archive_Research_Subagent", func=bridge.archive_research_subagent, description="Invoke the archived AI_Agents_Project for deep intelligence research (CVEs, Web Search, Historical Memory)."),
        Tool(name="Run_Specialized_Module", func=bridge.run_specialized_module, description="Execute a specialized exploit script from the modules/ directory (e.g., 'argus_deep_exploit.py', 'stealth_exploit.py'). Use this for deep file extraction or WAF bypass."),
        Tool(name="Run_Kali_Command", func=bridge.run_kali_command, description="Execute ANY raw command in the Kali Linux terminal (WSL). Use this for manual subdomain discovery (subfinder, assetfinder), fixing tools, or custom reconnaissance chains.")
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

                # Run the agent in a separate thread with a timeout to avoid UI hang
                def _run_agent():
                    return brain.ask(
                        f"CONSULT MEMORY FIRST using 'Query_Memory'. Then perform a comprehensive security analysis for {target}. "
                        f"If findings like SQLi, Path Traversal, or sensitive files already exist in memory, use 'Exploit_Suggester' and 'Smart_Web_Search' to CHAIN them and reach maximum impact (RCE). "
                        f"Finally, provide a deep risk assessment including the full attack chain.",
                        callbacks=[st_callback]
                    )

                analysis = {"output": "Analysis failed or timed out."}
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_run_agent)
                    try:
                        analysis = future.result(timeout=180)
                    except concurrent.futures.TimeoutError:
                        future.cancel()
                        st.error("Analysis timed out after 180 seconds. Consider running smaller tasks or increasing the timeout.")
                        status.update(label="Analysis Timed Out", state="error")

                st.markdown("### 📋 Final Security Report")

                # Check if we got a parsed dictionary or raw string
                final_report = ""
                if isinstance(analysis.get("output"), dict):
                    # It's the parsed Pydantic dict
                    report_dict = analysis["output"]
                    final_report = report_dict.get("output", str(report_dict))

                    # Display metrics in columns
                    col1, col2 = st.columns(2)
                    col1.metric("Overall Risk Score", f"{report_dict.get('overall_risk_score', 'N/A')}/10")
                    col2.metric("Findings Count", len(report_dict.get("findings", [])))

                    with st.expander("View Structured Data (JSON)"):
                        st.json(report_dict)
                else:
                    # It's the raw result string
                    final_report = analysis.get("output", str(analysis))

                # Render the final Markdown report using a safe code box for technical output
                st.code(final_report, language='markdown')

                status.update(label="Analysis Finished!", state="complete")

                # --- Export Feature (sanitize filename) ---
                safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', target.replace('https://', '').replace('http://', '').strip('/'))
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=final_report,
                    file_name=f"Argus_Report_{safe_name}.md",
                    mime="text/markdown"
                )
            except Exception as e:
                st.error(f"❌ Critical Error during AI Analysis: {str(e)}")
                st.warning("🔄 Suggestion: Restart Argus and try 'Force CPU Mode' if this is a GPU/CUDA error.")
                status.update(label="Analysis Failed", state="error")
