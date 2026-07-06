import streamlit as st
import sys
import os

# Ensure project root is in path for module access
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.config import ArgusConfig
from app.tools.tool_registry import WSLBridgeTools
from app.core.brain import ArgusBrain
from langchain_core.tools import Tool

config = ArgusConfig.load()

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
    model = config.model_name
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
        Tool(name="Crawl_Target", func=bridge.crawl_target, description="Discover internal links and entry points via curl/grep to expand the attack surface."),
        Tool(name="Query_Memory", func=bridge.get_intelligence_summary, description="Query the internal Shared Memory (Blackboard) for a summary of all findings."),
        Tool(name="Query_Knowledge_Graph", func=bridge.query_knowledge_graph, description="Access the Knowledge Graph to find cross-target relationships, shared infrastructure, and lateral movement paths."),
        Tool(name="Exploit_Suggester", func=bridge.suggest_payloads, description="Search PayloadsAllTheThings for test payloads."),
        Tool(name="Smart_Web_Search", func=bridge.smart_web_search, description="Search internet for CVEs/Exploits/Security info."),
        Tool(name="Run_Nikto", func=bridge.run_nikto, description="Run Nikto vulnerability scanner against a web target."),
        Tool(name="Run_FFUF", func=bridge.run_ffuf_discovery, description="Run FFUF for fast hidden path discovery."),
        Tool(name="System_Self_Heal", func=bridge.system_self_heal, description="Use this tool to autonomously install missing Python libraries (pip) or Kali system tools (apt) if you encounter a 'command not found' or 'ModuleNotFoundError'."),
        Tool(name="Archive_Research_Subagent", func=bridge.archive_research_subagent, description="Invoke the archived AI_Agents_Project for deep intelligence research (CVEs, Web Search, Historical Memory)."),
        Tool(name="Run_Kali_Command", func=bridge.run_kali_command, description="Execute ANY raw command in the Kali Linux terminal (WSL). Use this for manual subdomain discovery (subfinder, assetfinder), fixing tools, or custom reconnaissance chains.")
    ]
    return ArgusBrain(model_name, tools)

# Main Interface
target = st.text_input("🎯 Target URL", "https://example.com")

if st.button("RUN ANALYSIS"):
    if target:
        brain = load_brain(model)

        with st.status("🕵️ Argus Agent is thinking...", expanded=True) as status:
            try:
                st.write("Initializing autonomous security reasoning...")

                # Live per-phase progress: run_deterministic_recon calls this
                # right after each tool finishes, so results appear here as
                # they happen instead of only after the whole pipeline ends.
                def show_phase_progress(index, total, tool_name, observation):
                    st.write(f"**[{index}/{total}] {tool_name}**")
                    preview = observation if len(observation) <= 1500 else observation[:1500] + "\n... (truncated)"
                    st.code(preview, language="text")

                # The deterministic pipeline runs the fixed recon phases
                # itself in Python - it just needs the target, not an
                # elaborate instruction paragraph (there's no agent left
                # to interpret one).
                analysis = brain.ask(target, on_phase=show_phase_progress)

                st.markdown("### 📋 Final Security Report")

                report_dict = analysis.get("output")
                final_report = ""

                if isinstance(report_dict, dict) and "error" in report_dict:
                    # Synthesis failed outright (LLM error, or it echoed
                    # the schema instead of writing a real report after
                    # all retries) - say so plainly instead of dumping
                    # whatever garbage came back as if it were the report.
                    st.error(f"❌ Report synthesis failed: {report_dict.get('error')}")
                    st.warning(report_dict.get("message", ""))
                    with st.expander("Raw tool output (recon still ran successfully)"):
                        st.json(report_dict.get("raw_tool_observations", {}))
                    status.update(label="Analysis Failed", state="error")
                    final_report = None

                elif isinstance(report_dict, dict):
                    final_report = report_dict.get("output") or "(model returned no markdown output field)"

                    col1, col2 = st.columns(2)
                    col1.metric("Overall Risk Score", f"{report_dict.get('overall_risk_score', 'N/A')}/10")
                    col2.metric("Findings Count", len(report_dict.get("findings", [])))

                    with st.expander("View Structured Data (JSON)"):
                        st.json(report_dict)

                    st.markdown(final_report)
                    status.update(label="Analysis Finished!", state="complete")

                else:
                    final_report = str(analysis.get("output", analysis))
                    st.markdown(final_report)
                    status.update(label="Analysis Finished!", state="complete")

                if final_report:
                    st.download_button(
                        label="📥 Download Report (Markdown)",
                        data=final_report,
                        file_name=f"Argus_Report_{target.replace('https://', '').replace('http://', '').replace('/', '_')}.md",
                        mime="text/markdown"
                    )
            except Exception as e:
                st.error(f"❌ Critical Error during AI Analysis: {str(e)}")
                st.warning("🔄 Suggestion: Restart Argus and try 'Force CPU Mode' if this is a GPU/CUDA error.")
                status.update(label="Analysis Failed", state="error")