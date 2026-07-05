"""
Argus AI CLI - Unified entry point with --mode and --target flags.
"""
import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from core.tools import WSLBridgeTools
from core.agent import ArgusBrain
from core.safety import SafetyLayer
from langchain_core.tools import Tool


def build_tools(bridge: WSLBridgeTools) -> list:
    return [
        Tool(name="Check_Reachability", func=bridge.check_reachability,
             description="Verify if the target domain is reachable."),
        Tool(name="Subdomain_Enumeration", func=bridge.enumerate_subdomains,
             description="Discover subdomains to map the target's attack surface."),
        Tool(name="Get_Priority_Targets", func=bridge.get_priority_targets,
             description="Get ranked list of discovered subdomains from memory."),
        Tool(name="Recon_Suite", func=bridge.recon_suite,
             description="Execute parallel recon: WAF, Nmap, WhatWeb, Headers, Fuzzing."),
        Tool(name="Run_Nikto", func=bridge.run_nikto,
             description="Run Nikto web vulnerability scanner on the target."),
        Tool(name="Smart_Web_Search", func=bridge.smart_web_search,
             description="Search the web for CVEs, exploits, and technology information."),
        Tool(name="Query_Memory", func=bridge.get_intelligence_summary,
             description="Retrieve consolidated intelligence from the Blackboard."),
        Tool(name="Query_Knowledge_Graph", func=bridge.query_knowledge_graph,
             description="Find cross-target relationships in the Knowledge Graph."),
        Tool(name="Exploit_Suggester", func=bridge.suggest_payloads,
             description="Get relevant test payloads from PayloadsAllTheThings."),
        Tool(name="Generate_Report", func=bridge.generate_report,
             description="Generate final JSON and Markdown security report from all findings."),
    ]


def run_analysis(target_url: str, mode: str = "passive", dry_run: bool = False):
    print("\n" + "=" * 60)
    print(" ARGUS AI SECURITY FRAMEWORK v2.0")
    print("=" * 60)
    print(f"[*] Target  : {target_url}")
    print(f"[*] Mode    : {mode.upper()}")
    print(f"[*] Dry Run : {dry_run}")
    print(f"[*] Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # Safety validation
    safety = SafetyLayer()
    is_valid, reason = safety.validate_target(target_url, mode)
    if not is_valid:
        print(f"[SAFETY BLOCK] {reason}")
        sys.exit(1)

    if dry_run:
        print("[DRY RUN] Safety validation passed. Skipping actual scan.")
        print(f"[DRY RUN] Would scan: {target_url} in {mode} mode.")
        return

    model = os.getenv("SELECTED_MODEL", "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest")
    print(f"[*] Model   : {model}\n")

    bridge = WSLBridgeTools(scan_mode=mode)
    tools = build_tools(bridge)
    brain = ArgusBrain(model, tools)

    query = (
        f"Perform a comprehensive security analysis for {target_url} in {mode} mode. "
        f"Start with Check_Reachability, then Subdomain_Enumeration, Get_Priority_Targets, "
        f"Recon_Suite, Run_Nikto, Query_Memory, Query_Knowledge_Graph, Exploit_Suggester, "
        f"and finally call Generate_Report to produce the final JSON and Markdown reports."
    )

    try:
        started = datetime.now().isoformat()
        result = brain.ask(query)

        print("\n" + "=" * 60)
        print(" ARGUS FINAL REPORT")
        print("=" * 60)

        output = result.get("output", result)
        output_str = result.get("output_str", str(output))

        if isinstance(output, dict):
            print(f"Risk Score : {output.get('overall_risk_score', 'N/A')}/10")
            print(f"Summary    : {output.get('summary', '')[:200]}")
            findings = output.get('findings', [])
            print(f"Findings   : {len(findings)}")
            for f in findings:
                print(f"  [{f.get('severity', 'Info')}] {f.get('issue', '')} @ {f.get('target', '')}")
        else:
            print(output_str[:2000])

        # Log scan
        bridge.memory.log_scan_session(
            target=target_url, mode=mode,
            started_at=started, completed_at=datetime.now().isoformat(),
            findings_count=len(output.get('findings', [])) if isinstance(output, dict) else 0,
            risk_score=output.get('overall_risk_score', 0) if isinstance(output, dict) else 0
        )

    except KeyboardInterrupt:
        print("\n[!] Analysis interrupted by user.")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Argus AI Security Framework CLI v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python run_argus_cli.py --target https://example.com --mode passive\n  python run_argus_cli.py --dry-run"
    )
    parser.add_argument("--target", "-t", default="https://example.com",
                        help="Target URL to analyze (default: https://example.com)")
    parser.add_argument("--mode", "-m", choices=["passive", "aggressive"], default="passive",
                        help="Scan mode (default: passive)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate configuration without running actual scan")
    args = parser.parse_args()
    run_analysis(args.target, args.mode, args.dry_run)
