from app.core.brain import ArgusBrain
from app.tools.tool_registry import WSLBridgeTools
from langchain_core.tools import Tool
import os

def run_autonomous_reasoning():
    bridge = WSLBridgeTools()
    model = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"
    
    tools = [
        Tool(name="Check_Reachability", func=bridge.check_reachability, description="Verify if the target domain is reachable."),
        Tool(name="Subdomain_Enumeration", func=bridge.enumerate_subdomains, description="Discover subdomains."),
        Tool(name="Recon_Suite", func=bridge.recon_suite, description="Execute advanced recon."),
        Tool(name="Query_Memory", func=bridge.get_intelligence_summary, description="Query the internal Shared Memory."),
        Tool(name="Query_Knowledge_Graph", func=bridge.query_knowledge_graph, description="Access the Knowledge Graph."),
        Tool(name="Exploit_Suggester", func=bridge.suggest_payloads, description="Search for test payloads."),
        Tool(name="Smart_Web_Search", func=bridge.smart_web_search, description="Search internet for security info."),
        Tool(name="Run_Nikto", func=bridge.run_nikto, description="Run Nikto."),
        Tool(name="Run_FFUF", func=bridge.run_ffuf_discovery, description="Run FFUF.")
    ]
    
    brain = ArgusBrain(model, tools)
    
    # Custom query for the reasoning phase
    query = (
        "CONSULT MEMORY FIRST. Do NOT run Recon_Suite, Check_Reachability, or Subdomain_Enumeration. "
        "Use 'Query_Memory' to retrieve the existing findings for testasp.vulnweb.com. "
        "Based on the confirmed Path Traversal (web.config) and the WAF-blocked SQLi, "
        "use 'Exploit_Suggester' for SQLi bypasses and 'Smart_Web_Search' for IIS 8.5 known vulnerabilities. "
        "Finally, synthesize a Professional Security Report with your autonomous reasoning."
    )
    
    print("\n[!] ARGUS AUTONOMOUS REASONING START")
    result = brain.ask(query)
    print("\n" + "="*60)
    print("🛡️ ARGUS AUTONOMOUS FINAL REPORT")
    print("="*60)
    
    if isinstance(result, dict) and "output" in result:
        print(result["output"])
    else:
        print(result)

if __name__ == "__main__":
    run_autonomous_reasoning()
