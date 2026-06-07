import os
import sys
import argparse
from core.tools import WSLBridgeTools
from core.agent import ArgusBrain
from langchain_core.tools import Tool
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

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
        Tool(name="Run_FFUF", func=bridge.run_ffuf_discovery, description="Run FFUF for fast hidden path discovery.")
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
