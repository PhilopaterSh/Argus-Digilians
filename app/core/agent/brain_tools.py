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
from typing import Optional

from langchain_core.tools import Tool

from app.tools.tool_registry import WSLBridgeTools

# specs/020 (multi-agent role separation, feature-flagged off by default -
# see config.yaml's enable_multi_agent_roles) FR-002's tool partition, kept
# here as the one place that lists which tool names belong to which role
# (Constitution IX) - `build_argus_tools(bridge, role=...)` below filters
# the full 19-tool list against this mapping rather than maintaining a
# second, separately-constructed tool list per role.
# Collector: reconnaissance/discovery only. Exploiter: vulnerability
# scanning/exploitation only. Planner/Summarizer: read-only memory access,
# no execution tools at all (FR-002 - "no direct execution tools"), so they
# have no entry here; build_argus_tools() returns just
# {Query_Memory, Query_Knowledge_Graph} for either directly.
# Reflective_Pre_Verify/System_Self_Heal are generic utilities relevant to
# any role that runs commands, so both Collector and Exploiter get them.
ROLE_TOOL_PARTITIONS = {
    "collector": {
        "Check_Reachability", "Subdomain_Enumeration", "Recon_Suite",
        "Crawl_Target", "Secret_Scanner", "Smart_Web_Search",
        "Task_Difficulty_Assessment", "Archive_Research_Subagent",
        "Reflective_Pre_Verify", "System_Self_Heal", "Fuzz_Sensitive_Files",
    },
    "exploiter": {
        "Run_Nikto", "Run_FFUF", "Exploit_Suggester", "Advanced_Evasion_Probe",
        "Run_Kali_Command", "Reflective_Pre_Verify", "System_Self_Heal",
        "Path_Traversal_Scan",
    },
}
_PLANNER_SUMMARIZER_TOOLS = {"Query_Memory", "Query_Knowledge_Graph"}


def build_argus_tools(bridge: WSLBridgeTools, role: Optional[str] = None) -> list[Tool]:
    """Wrap WSLBridgeTools methods as LangChain Tools for ArgusBrain's ReAct agent.

    Args:
        bridge (WSLBridgeTools): The tool facade whose bound methods back each
            Tool's `func`.
        role (str, optional): One of `"collector"`, `"exploiter"`,
            `"planner"`, `"summarizer"` (specs/020, feature-flagged off by
            default) to return only that role's tool subset per
            `ROLE_TOOL_PARTITIONS`/`_PLANNER_SUMMARIZER_TOOLS`. `None`
            (default) returns the full 19-tool list, unchanged from before
            this parameter existed - every existing caller (`019` and
            earlier) is unaffected.

    Returns:
        list[Tool]: The full 19-tool list covering recon, memory/graph
        queries, scanning, exploitation research, reflective
        self-verification, and raw command execution when `role` is `None`
        (see the module docstring's 2026-07-09 audit for how this list was
        assembled) - or just `role`'s subset when specified.
        `run_specialized_module` is the one intentional omission from the
        full list - it's no longer present on `WSLBridgeTools` (the
        modules/ scripts it invoked were not migrated during the
        tool-registry refactor).
    """
    all_tools = [
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
            description="Background/OSINT research beyond a quick search (company history, prior incidents, broader context). Currently a web-search-backed lookup - see SmartWebSearch.archive_research_subagent()'s docstring for what changed 2026-07-19.",
        ),
        Tool(
            name="Run_Kali_Command",
            func=bridge.run_kali_command,
            description="Execute ANY raw command in the Kali Linux terminal (WSL). Use this for manual subdomain discovery (subfinder, assetfinder), fixing tools, or custom reconnaissance chains.",
        ),
        Tool(
            name="Fuzz_Sensitive_Files",
            func=bridge.fuzz_sensitive_files,
            description="Check common sensitive file paths (.env, .git/config, backup.sql, etc.) for accidental exposure.",
        ),
        Tool(
            name="Path_Traversal_Scan",
            func=bridge.run_traversal_scan,
            description="Dedicated multi-parameter, multi-encoding path-traversal/LFI probe - content-verified against /etc/passwd, win.ini, boot.ini, and web.config signatures, not HTTP status alone.",
        ),
    ]
    if role is None:
        return all_tools
    if role in ("planner", "summarizer"):
        allowed = _PLANNER_SUMMARIZER_TOOLS
    else:
        allowed = ROLE_TOOL_PARTITIONS.get(role, set())
    return [t for t in all_tools if t.name in allowed]


def partition_tools_by_role(tools: list) -> dict:
    """Split an already-built flat tool list into role subsets, using the
    same `ROLE_TOOL_PARTITIONS` mapping `build_argus_tools(bridge, role=...)`
    filters against - so a caller that already has `ArgusBrain`'s flat
    19-tool list (no `WSLBridgeTools` reference of its own) doesn't need to
    rebuild tools from a bridge just to get the specs/020 multi-role
    partition (Constitution IX - one partition definition, two entry points).

    Args:
        tools (list): Flat list of `Tool` objects (e.g. `ArgusBrain.tools`).

    Returns:
        dict: `{"collector": [...], "exploiter": [...]}` - tools whose name
        isn't in either partition (there shouldn't be any, given
        `ROLE_TOOL_PARTITIONS` covers all 17) are silently omitted from
        both, matching `build_argus_tools(role=...)`'s own filtering
        behavior.
    """
    return {
        "collector": [t for t in tools if t.name in ROLE_TOOL_PARTITIONS["collector"]],
        "exploiter": [t for t in tools if t.name in ROLE_TOOL_PARTITIONS["exploiter"]],
    }
