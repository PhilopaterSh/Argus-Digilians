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

# Logic Initialization - created before the sidebar so the memory
# maintenance button below can reference bridge.memory directly.
bridge = WSLBridgeTools()

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

    st.markdown("---")
    st.subheader("🧠 Execution Mode")
    exec_mode = st.radio(
        "Choose how Argus decides what to run",
        ["Deterministic Pipeline", "Agentic (ReAct) - test"],
        help=(
            "Deterministic Pipeline: fixed Python phase list + chaining "
            "rules, no LLM tool-selection, reliable but not adaptive.\n\n"
            "Agentic (ReAct): the LLM chooses which tool to call at each "
            "step via ARGUS_ADAPTIVE_AGENT_TEMPLATE. More capable in "
            "principle, but WhiteRabbitNeo-7B has repeatedly failed to "
            "follow this format reliably in testing - this mode is here "
            "so you can verify whether recent tool-level fixes changed that."
        ),
    )

    st.markdown("---")
    st.subheader("🧹 Memory Maintenance")
    st.caption(
        "Earlier bugs could store a full instruction sentence as if it "
        "were a target domain. This only removes entries that look like "
        "that - real scanned targets are left untouched."
    )
    if st.button("Purge polluted memory entries"):
        try:
            removed = bridge.memory.purge_invalid_targets()
            if removed:
                st.success(f"Removed {removed} polluted entr{'y' if removed == 1 else 'ies'} from memory.")
            else:
                st.info("No polluted entries found.")
        except AttributeError:
            st.error(
                "Could not find `bridge.memory` - if WSLBridgeTools exposes "
                "its ArgusMemory instance under a different attribute name, "
                "update this button to match."
            )
        except Exception as e:
            st.error(f"Purge failed: {e}")


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

def render_analysis_result(analysis, target, status):
    """Shared result display for both execution modes - the shape of
    `analysis["output"]` is the same whether it came from the
    deterministic pipeline or the agentic path (dict with real fields,
    dict with "error", or a raw string fallback)."""
    st.markdown("### 📋 Final Security Report")

    report_dict = analysis.get("output")
    final_report = ""

    if isinstance(report_dict, dict) and "error" in report_dict:
        st.error(f"❌ Report synthesis failed: {report_dict.get('error')}")
        st.warning(report_dict.get("message", ""))
        with st.expander("Raw tool output (recon still ran successfully)"):
            st.json(report_dict.get("raw_tool_observations", {}))
        status.update(label="Analysis Failed", state="error")
        return None

    elif isinstance(report_dict, dict):
        final_report = report_dict.get("output") or "(model returned no markdown output field)"

        if report_dict.get("_warning"):
            st.warning(f"⚠️ {report_dict['_warning']}")

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

    return final_report


if st.button("RUN ANALYSIS"):
    if target:
        brain = load_brain(model)

        with st.status("🕵️ Argus Agent is thinking...", expanded=True) as status:
            try:
                st.write("Initializing autonomous security reasoning...")
                final_report = None

                if exec_mode == "Deterministic Pipeline":
                    # Live per-phase progress: run_deterministic_recon calls
                    # this right after each tool finishes, so results appear
                    # here as they happen instead of only at the end.
                    def show_phase_progress(index, total, tool_name, observation):
                        st.write(f"**[{index}/{total}] {tool_name}**")
                        preview = observation if len(observation) <= 1500 else observation[:1500] + "\n... (truncated)"
                        st.code(preview, language="text")

                    analysis = brain.ask(target, on_phase=show_phase_progress)

                else:
                    # Agentic mode: the LLM chooses tools itself, so it
                    # needs a natural-language instruction, not a bare
                    # target - there's no fixed phase list to run it
                    # through. No on_phase callback here since there's no
                    # deterministic phase loop to hook into; if you want
                    # to see the agent's live thoughts, that would need a
                    # LangChain callback wired into ask_agentic() instead.
                    st.info("Agentic mode: no live per-step progress - the agent runs to completion or failure, then reports.")
                    instruction = (
                        f"CONSULT MEMORY FIRST using 'Query_Memory'. Then perform a comprehensive "
                        f"security analysis for {target}. If findings like SQLi, Path Traversal, or "
                        f"sensitive files already exist in memory, use 'Exploit_Suggester' and "
                        f"'Smart_Web_Search' to CHAIN them and reach maximum impact (RCE). Finally, "
                        f"provide a deep risk assessment including the full attack chain."
                    )
                    analysis = brain.ask_agentic(instruction)

                final_report = render_analysis_result(analysis, target, status)

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