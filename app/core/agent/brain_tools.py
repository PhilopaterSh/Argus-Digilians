"""Canonical tool list for ArgusBrain's ReAct loop (specs/017-restore-react-agent).

Previously this exact list was hand-copied into four separate deprecated GUI
files (app/GUI/{app,argus_gui,gui_main}.py, desktop_gui.py) - one canonical
builder here instead, per Constitution IX (Single Source of Truth).
"""
from langchain_core.tools import Tool

from app.tools.tool_registry import WSLBridgeTools


def build_argus_tools(bridge: WSLBridgeTools) -> list[Tool]:
    """Wrap WSLBridgeTools methods as LangChain Tools for ArgusBrain's ReAct agent.

    Args:
        bridge (WSLBridgeTools): The tool facade whose bound methods back each
            Tool's `func`.

    Returns:
        list[Tool]: 12 tools covering recon, memory/graph queries, scanning,
        exploitation research, and raw command execution. Matches the
        original 13-tool list from the historical `PHILOPATERSH` branch
        GUI, minus `run_specialized_module` (no longer present on
        `WSLBridgeTools` - the modules/ scripts it invoked were not
        migrated during the tool-registry refactor).
    """
    return [
        Tool(
            name="Check_Reachability",
            func=bridge.check_reachability,
            description="Verify if the target domain is reachable before scanning.",
        ),
        Tool(
            name="Subdomain_Enumeration",
            func=bridge.enumerate_subdomains,
            description="Discover subdomains to map the target's attack surface.",
        ),
        Tool(
            name="Recon_Suite",
            func=bridge.recon_suite,
            description="Execute parallel advanced recon (WAF, Nmap, WhatWeb, HTTP Headers, Spider) inside Kali.",
        ),
        Tool(
            name="Query_Memory",
            func=bridge.get_intelligence_summary,
            description="Query the internal Shared Memory (Blackboard) for a summary of all findings.",
        ),
        Tool(
            name="Query_Knowledge_Graph",
            func=bridge.query_knowledge_graph,
            description="Access the Knowledge Graph to find cross-target relationships, shared infrastructure, and lateral movement paths.",
        ),
        Tool(
            name="Exploit_Suggester",
            func=bridge.suggest_payloads,
            description="Search PayloadsAllTheThings for test payloads.",
        ),
        Tool(
            name="Smart_Web_Search",
            func=bridge.smart_web_search,
            description="Search internet for CVEs/Exploits/Security info.",
        ),
        Tool(
            name="Run_Nikto",
            func=bridge.run_nikto,
            description="Run Nikto vulnerability scanner against a web target.",
        ),
        Tool(
            name="Run_FFUF",
            func=bridge.run_ffuf_discovery,
            description="Run FFUF for fast hidden path discovery.",
        ),
        Tool(
            name="System_Self_Heal",
            func=bridge.system_self_heal,
            description="Use this tool to autonomously install missing Python libraries (pip) or Kali system tools (apt) if you encounter a 'command not found' or 'ModuleNotFoundError'.",
        ),
        Tool(
            name="Archive_Research_Subagent",
            func=bridge.archive_research_subagent,
            description="Invoke the archived AI_Agents_Project for deep intelligence research (CVEs, Web Search, Historical Memory).",
        ),
        Tool(
            name="Run_Kali_Command",
            func=bridge.run_kali_command,
            description="Execute ANY raw command in the Kali Linux terminal (WSL). Use this for manual subdomain discovery (subfinder, assetfinder), fixing tools, or custom reconnaissance chains.",
        ),
    ]
