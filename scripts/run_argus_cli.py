import os
import sys
import argparse

# Ensure the project root is on the import path before importing app modules.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.tools.tool_registry import WSLBridgeTools
from app.core.agent.brain import ArgusBrain
from app.core.config import ArgusConfig
from langchain_core.tools import Tool
from dotenv import load_dotenv

load_dotenv()
config = ArgusConfig.load()

def run_analysis(target_url):
    bridge = WSLBridgeTools()
    model = config.model_name
    
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
        Tool(name="Advanced_Evasion_Probe", func=bridge.advanced_vuln_probe, description="Perform targeted, WAF-evasive probes for SQLi and Path Traversal.")
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
        print("[REPORT] ARGUS AGENT FINAL REPORT")
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


