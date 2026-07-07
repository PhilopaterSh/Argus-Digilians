import re
import json
from datetime import datetime

class ReconService:
    """Handles subdomain enumeration, prioritization, and broad reconnaissance suites."""

    def __init__(self, runner, memory, fuzzer=None, secret_analyzer=None, report_writer=None):
        self.runner = runner
        self.memory = memory
        self.fuzzer = fuzzer
        self.secret_analyzer = secret_analyzer
        self.report_writer = report_writer
        self.last_recon_results = None

    def enumerate_subdomains(self, domain):
        """Discovers subdomains using subfinder and assetfinder in parallel."""
        print(f"[*] Starting Subdomain Enumeration for: {domain}")
        
        # Parallel execution in background via WSL
        cmd = f"subfinder -d {domain} -silent & assetfinder --subs-only {domain} & wait"
        res = self.runner.run(cmd)
        
        if res.strip():
            subdomains = list(set([s.strip() for s in res.strip().splitlines() if s.strip()]))
            print(f"[+] Discovered {len(subdomains)} unique subdomains.")
            
            # Upsert into knowledge graph
            for sub in subdomains:
                self.memory.upsert_target(sub)
            
            # Save structure to memory for the blackboard
            if hasattr(self.memory, 'save_recon_data'):
                self.memory.save_recon_data(domain, {"subdomains": subdomains})
            
            return f"```\n{res}\n```"
        
        return "No subdomains discovered or tool failed."

    def prioritize_targets(self, targets):
        """Uses HTTP probing (httpx) to find alive targets and identify high-value ones."""
        if not targets:
            return "No targets provided for prioritization."
            
        target_list = ",".join(targets) if isinstance(targets, list) else targets
        print(f"[*] Prioritizing {len(targets) if isinstance(targets, list) else 'targets'} via HTTPX...")
        
        cmd = f"echo '{target_list.replace(',', '\n')}' | httpx -silent -sc -title -td"
        res = self.runner.run(cmd)
        
        # Parse results and update memory
        lines = res.strip().splitlines()
        for line in lines:
            parts = line.split()
            if len(parts) >= 1:
                url = parts[0]
                status = parts[1] if len(parts) > 1 else "unknown"
                self.memory.add_finding(url, "httpx", "status", status, f"Alive target with status {status}")

        return f"```\n{res}\n```"

    def recon_suite(self, url, selected_targets=None):
        """Runs expanded recon with smart target prioritization and parallel execution."""
        clean_target = url.replace("https://", "").replace("http://", "").rstrip('/')
        print(f"[*] Starting Full Recon Suite for: {clean_target}")

        results = {}

        # Bounded per-command so one slow/unresponsive tool can't consume the
        # entire outer agent-run budget (scripts/run_agent.py's
        # AGENT_TIMEOUT_SECONDS) and silently strand the graph on this node.
        # 1. Tech Stack (whatweb)
        print(f"[*] Identifying Tech Stack for {clean_target}...")
        results['tech'] = self.runner.run(f"whatweb {url} --aggression 3", timeout=90)

        # 2. Port Scan (nmap - lightweight)
        print(f"[*] Scanning Ports for {clean_target}...")
        results['ports'] = self.runner.run(f"nmap -sV -T4 --top-ports 100 {clean_target}", timeout=180)

        # 3. DNS Recon
        print(f"[*] DNS Enumeration for {clean_target}...")
        results['dns'] = self.runner.run(f"dig ANY {clean_target} +short", timeout=20)

        self.last_recon_results = results
        
        # Save results to memory
        self.memory.add_finding(clean_target, "recon_suite", "full_scan", "completed", json.dumps(results))
        
        if self.report_writer:
            self.report_writer.save_json_report(clean_target, results)

        report = f"--- [SAT] FULL RECON REPORT: {clean_target} ---\n"
        report += f"Tech: {results['tech'][:200]}...\n"
        report += f"Ports: {results['ports'][:500]}...\n"
        
        return f"```\n{report}\n```"
