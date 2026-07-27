import re
import json
from datetime import datetime

from app.tools.utils import normalize_domain_for_memory

class ReconService:
    """Handles subdomain enumeration, prioritization, and broad reconnaissance suites."""

    def __init__(self, runner, memory, fuzzer=None, secret_analyzer=None, report_writer=None):
        """Wire up the collaborators this service delegates to.

        Args:
            runner: Object with a `run(command, timeout=None)` method
                (shared CommandRunner).
            memory: ArgusMemory-like object used to record findings and
                upsert targets.
            fuzzer: Optional fuzzing collaborator (currently unused by any
                method on this class).
            secret_analyzer: Optional SecretAnalyzer-like collaborator
                (currently unused by any method on this class).
            report_writer: Optional object with a `save_json_report(...)`
                method, used by `recon_suite` if provided.
        """
        self.runner = runner
        self.memory = memory
        self.fuzzer = fuzzer
        self.secret_analyzer = secret_analyzer
        self.report_writer = report_writer
        self.last_recon_results = None

    def enumerate_subdomains(self, domain):
        """Discovers subdomains using subfinder and assetfinder in parallel.

        Args:
            domain (str): The root domain to enumerate subdomains for.

        Returns:
            str: A fenced code block of the raw discovered-subdomain
            output, or "No subdomains discovered or tool failed." if
            nothing came back.
        """
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
        """Uses HTTP probing (httpx) to find alive targets and identify high-value ones.

        Args:
            targets (list[str] | str): Target hosts, either as a list or
                an already comma-separated string.

        Returns:
            str: A fenced code block of the raw httpx output, or
            "No targets provided for prioritization." if `targets` is
            empty.
        """
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

    @staticmethod
    def _nmap_needs_fallback(nmap_output):
        """True if the primary -sV scan didn't produce a usable port list.

        Covers both failure modes seen behind a WAF/CDN (e.g. Cloudflare):
        the command_runner-level timeout/error (slow per-port -sV service
        probing through a filtering proxy), and nmap completing "cleanly"
        but reporting the host down because its default ICMP/TCP
        host-discovery ping got dropped, which -Pn below skips entirely.

        Args:
            nmap_output (str): The primary `-sV` scan's raw output (or
                error message).

        Returns:
            bool: True if a lighter `-Pn` fallback scan should be tried
            (empty/error output, a "host seems down"/"0 hosts up" report,
            or no `/tcp` port line at all); False if the output already
            has a usable port list.
        """
        if not nmap_output:
            return True
        lowered = nmap_output.lower()
        if lowered.startswith("error:") or lowered.startswith("error ("):
            return True
        if "host seems down" in lowered or "0 hosts up" in lowered:
            return True
        return "/tcp" not in nmap_output

    def recon_suite(self, url, selected_targets=None):
        """Runs expanded recon with smart target prioritization and parallel execution.

        Args:
            url (str): Target URL/domain to run tech-stack, port-scan, and
                DNS recon against.
            selected_targets: Currently unused by this method's own body -
                accepted for call-site compatibility.

        Returns:
            str: A fenced code block summarizing the tech stack and port
            scan results.
        """
        clean_target = normalize_domain_for_memory(url)
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

        if self._nmap_needs_fallback(results['ports']):
            # A full -sV top-100 scan is slow (per-port service
            # fingerprinting) and behind a WAF/CDN like Cloudflare it
            # routinely times out or nmap's default host-discovery ping
            # gets dropped, reporting the host "down" even though it's
            # clearly serving traffic (whatweb above just proved that).
            # Retry with a much lighter, faster degraded scan: -Pn skips
            # host discovery entirely and dropping -sV avoids the slow
            # per-port probing, so it has a real chance of getting a
            # genuine nmap-confirmed answer instead of just giving up.
            print(f"[!] Primary nmap scan failed/inconclusive for {clean_target}: {results['ports'][:150]}")
            print("[*] Retrying with a lighter -Pn degraded scan (skips host-discovery ping)...")
            fallback_output = self.runner.run(f"nmap -Pn -T4 --top-ports 20 {clean_target}", timeout=60)
            results['ports_scan_degraded'] = True
            if not self._nmap_needs_fallback(fallback_output):
                results['ports'] = fallback_output
            else:
                print(f"[!] Degraded nmap scan also inconclusive for {clean_target}: {fallback_output[:150]}")
                results['ports'] = fallback_output

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
