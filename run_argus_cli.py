import os
import sys
import argparse
from app.tools.tool_registry import WSLBridgeTools
from app.core.brain import ArgusBrain
from langchain_core.tools import Tool
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Heuristic patch: increase websockets keepalive defaults to reduce
# spurious keepalive ping timeouts (close code 1011) when a lower-level
# dependency opens websocket connections without explicit ping settings.
# This is intentionally resilient: if websockets isn't installed or the
# internal API changes, fall back silently.
try:
    from websockets.legacy.protocol import WebSocketCommonProtocol
    _orig_ws_init = WebSocketCommonProtocol.__init__

    def _patched_ws_init(self, *args, **kwargs):
        # Set more forgiving defaults if not explicitly provided by callers.
        # Keep None as-is (disables keepalive/timeouts when intentionally set).
        kwargs.setdefault("ping_interval", 30)
        kwargs.setdefault("ping_timeout", 60)
        # Sanity clamp (avoid accidentally setting extremely small values).
        pi = kwargs.get("ping_interval")
        pt = kwargs.get("ping_timeout")
        if pi is not None and isinstance(pi, (int, float)) and pi < 5:
            kwargs["ping_interval"] = 30
        if pt is not None and isinstance(pt, (int, float)) and pt < 10:
            kwargs["ping_timeout"] = 60
        return _orig_ws_init(self, *args, **kwargs)

    WebSocketCommonProtocol.__init__ = _patched_ws_init
except Exception:
    # Ignore failures to avoid breaking startup when websockets isn't present
    pass


def run_analysis(target_url):
    bridge = WSLBridgeTools()
    # Using the primary model defined in the project
    model = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"
    
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
        Tool(name="Crawl_Target", func=bridge.crawl_target, description="Discover internal links and entry points to expand attack surface."),
        Tool(name="Advanced_Evasion_Probe", func=bridge.advanced_vuln_probe, description="Perform targeted, WAF-evasive probes for SQLi and Path Traversal."),
        Tool(name="Reflective_Pre_Verify", func=bridge.pre_execute_verify, description="Check commands for malformed parameters, illegal syntax, or missing tools before running."),
        Tool(name="Reflective_Post_Verify", func=bridge.post_execute_verify, description="Inspect output headers, content size, or redirect parameters to filter out honeypots or false positives."),
        Tool(name="Task_Difficulty_Assessment", func=bridge.task_difficulty_assessment, description="Compute TDA scores for target selection based on expected path length, version confidence, and history."),
        Tool(name="ZERO_APT_Simulation", func=bridge.run_zero_apt_simulation, description="Run a three-party interactive simulation (Attacker vs Active Defender L1-L3 with independent Judge) and export a STIX 2.0 report.")
    ]
    
    brain = ArgusBrain(model, tools)
    
    print(f"\n[!] ARGUS CLI MODE ACTIVATED")
    print(f"[*] Target: {target_url}")
    print(f"[*] Model: {model}")
    print("[*] Initializing autonomous security reasoning...\n")
    print("-" * 60)

    try:
        query = f"Perform a comprehensive security analysis for {target_url}. Start with reachability, then map the attack surface, and finally provide a deep risk assessment."
        # Brain.ask returns a dict with "output" (parsed JSON) or raw result
        result = brain.ask(query)
        
        print("\n" + "="*60)
        print("🛡️ ARGUS AGENT FINAL REPORT")
        print("="*60)
        
        if isinstance(result, dict) and "output" in result:
            output = result["output"]
            if isinstance(output, dict):
                import json
                print(json.dumps(output, indent=4))
            else:
                print(output)
        else:
            print(result)
            
    except KeyboardInterrupt:
        print("\n[!] Analysis interrupted by user.")
    except Exception as e:
        print(f"\n[!] An error occurred during execution: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Argus AI CLI")
    parser.add_argument("target", nargs="?", default="https://cultbeauty.co.uk/", help="Target URL")
    args = parser.parse_args()
    run_analysis(args.target)
