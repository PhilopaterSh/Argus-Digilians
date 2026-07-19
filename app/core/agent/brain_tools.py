"""Canonical tool list for ArgusBrain's ReAct loop (specs/017-restore-react-agent).

Previously this exact list was hand-copied into four separate deprecated GUI
files (app/GUI/{app,argus_gui,gui_main}.py, desktop_gui.py) - one canonical
builder here instead, per Constitution IX (Single Source of Truth).

2026-07-09 audit (specs/018 CHK090): this "canonical" list turned out to be
missing 5 real, working `WSLBridgeTools` capabilities that a *sixth*,
independently-drifted copy (`scripts/run_argus_cli.py`) still had -
`crawl_target`/`advanced_vuln_probe`/`verify_command`/`assess_difficulty`
were in that copy but not here; `analyze_secrets` was in neither. The
"single canonical builder" had silently become incomplete relative to a
copy it was supposed to have replaced. All 5 added below;
`scripts/run_argus_cli.py` now imports this function instead of maintaining
its own list.
"""
from langchain_core.tools import Tool

from app.tools.tool_registry import WSLBridgeTools


def build_argus_tools(bridge: WSLBridgeTools) -> list[Tool]:
    """Wrap WSLBridgeTools methods as LangChain Tools for ArgusBrain's ReAct agent.

    Args:
        bridge (WSLBridgeTools): The tool facade whose bound methods back each
            Tool's `func`.

    Returns:
        list[Tool]: 17 tools covering recon, memory/graph queries, scanning,
        exploitation research, reflective self-verification, and raw command
        execution - the true union of every tool any of this project's
        historical tool lists ever exposed (see the module docstring's
        2026-07-09 audit), not just the 12 that happened to survive the
        original consolidation. `run_specialized_module` is the one
        intentional omission - it's no longer present on `WSLBridgeTools`
        (the modules/ scripts it invoked were not migrated during the
        tool-registry refactor).
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
            name="Crawl_Target",
            func=bridge.crawl_target,
            description="Discover internal links and entry points to expand the attack surface.",
        ),
        Tool(
            name="Secret_Scanner",
            func=bridge.analyze_secrets,
            description="Scan the page body and JS files for leaked API keys, credentials, and secrets (AWS/Google keys, Slack webhooks, env vars).",
        ),
        Tool(
            name="Advanced_Evasion_Probe",
            func=bridge.advanced_vuln_probe,
            description="Perform targeted, WAF-evasive probes for SQL injection and Path Traversal - actually attempts exploitation, not just suggestion.",
        ),
        Tool(
            name="Reflective_Pre_Verify",
            func=bridge.verify_command,
            description="Check a command for malformed parameters, illegal syntax, or missing tools before running it.",
        ),
        Tool(
            name="Task_Difficulty_Assessment",
            func=bridge.assess_difficulty,
            description="Compute a Task Difficulty Assessment (TDA) score for target selection, based on expected path length, version confidence, and history.",
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
