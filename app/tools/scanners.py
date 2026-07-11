import os
from datetime import datetime

from app.tools.utils import normalize_domain_for_memory


class VulnerabilityScanners:
    """Specialized service for running automated scanners like Nikto and FFUF."""

    def __init__(self, runner, memory):
        """Store the shared command runner and memory service.

        Args:
            runner: Object with a `run(command)` method that executes a
                shell command (via WSL/SSH) and returns its output as a str.
            memory (ArgusMemory): Blackboard memory service used to persist
                scan findings.
        """
        self.runner = runner
        self.memory = memory

    @staticmethod
    def _connection_failed(nikto_output: str) -> bool:
        """True if Nikto never actually reached the target.

        Args:
            nikto_output (str): Raw stdout from the `nikto` command.

        Returns:
            bool: True on an explicit connection failure (e.g. the target
            port is closed/filtered), False otherwise - including a clean
            scan that simply found nothing.
        """
        lowered = nikto_output.lower()
        return "unable to connect" in lowered or "[fail]" in lowered

    def run_nikto(self, url):
        """Runs Nikto vulnerability scanner inside Kali against a web target.

        Args:
            url (str): Target URL. If Nikto can't connect (the given scheme's
                port is closed - a live run against scanme.nmap.org called
                this with `https://` while only port 80/http was actually
                open, per its own earlier Nmap scan), one retry is made with
                the opposite scheme before giving up, rather than trusting
                the caller to have picked the right one.

        Returns:
            str: The Nikto report text (from whichever scheme succeeded, or
            the original attempt's output if both fail), prefixed with the
            saved report's file path.
        """
        print(f"[*] Starting Nikto Vulnerability Scan for: {url}")

        output_dir = "reports/nikto"
        os.makedirs(output_dir, exist_ok=True)

        clean_target = url.replace("https://", "").replace("http://", "").rstrip('/').replace("/", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        # No .txt suffix here - nikto's own `-Format txt -o <path>` always appends
        # the format extension itself, regardless of what's already on the path.
        # Passing a pre-suffixed path produced real ".txt.txt" files on disk
        # (confirmed in reports/nikto/) while this method's own return message
        # kept reporting the un-suffixed (wrong) path.
        base_name = f"nikto_{clean_target}_{timestamp}"
        output_stem = f"{output_dir}/{base_name}"
        output_path = f"{output_stem}.txt"

        cmd = f"nikto -h {url} -nointeractive -maxtime 120s -Format txt -o {output_stem}"
        res = self.runner.run(cmd)

        if self._connection_failed(res):
            if url.startswith("https://"):
                fallback_url = "http://" + url[len("https://"):]
            elif url.startswith("http://"):
                fallback_url = "https://" + url[len("http://"):]
            else:
                fallback_url = None
            if fallback_url:
                print(f"[!] Nikto could not connect to {url} - retrying with {fallback_url}...")
                fallback_cmd = f"nikto -h {fallback_url} -nointeractive -maxtime 120s -Format txt -o {output_stem}"
                fallback_res = self.runner.run(fallback_cmd)
                if not self._connection_failed(fallback_res):
                    url, res = fallback_url, fallback_res

        findings = [l for l in res.split('\n') if l.strip().startswith("+")]
        if findings:
            target_for_mem = normalize_domain_for_memory(url)
            for f in findings:
                self.memory.add_finding(target_for_mem, "nikto", "vulnerability", f, "Potential vulnerability detected")

        return f"--- [TOOLS] NIKTO VULNERABILITY REPORT (Saved to {output_path}) ---\n{res}"

    def run_ffuf_discovery(self, url):
        """Runs FFUF for fast directory discovery inside Kali.

        Args:
            url (str): Target URL. Empty output is ambiguous - it could mean
                a clean scan with nothing found, or that FFUF couldn't
                connect at all (wrong scheme/closed port). One retry with
                the opposite scheme is attempted before concluding nothing
                was found, mirroring `run_nikto`'s same fallback.

        Returns:
            str: A summary of discovered paths, or a "no notable paths"
            message if both scheme attempts came back empty.
        """
        clean_url = url.rstrip('/')
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"

        print(f"[*] Starting FFUF Path Discovery for: {clean_url}")
        cmd = f"ffuf -w {wordlist} -u {clean_url}/FUZZ -mc 200,301,302 -s -t 50 -maxtime 110"
        res = self.runner.run(cmd)

        if not res.strip():
            fallback_url = None
            if clean_url.startswith("https://"):
                fallback_url = "http://" + clean_url[len("https://"):]
            elif clean_url.startswith("http://"):
                fallback_url = "https://" + clean_url[len("http://"):]
            if fallback_url:
                print(f"[!] FFUF found nothing on {clean_url} - retrying with {fallback_url}...")
                fallback_cmd = f"ffuf -w {wordlist} -u {fallback_url}/FUZZ -mc 200,301,302 -s -t 50 -maxtime 110"
                fallback_res = self.runner.run(fallback_cmd)
                if fallback_res.strip():
                    url, clean_url, res = fallback_url, fallback_url, fallback_res

        if res.strip():
            paths = res.strip().splitlines()
            clean_target = normalize_domain_for_memory(url)
            for p in paths[:20]:
                self.memory.add_finding(clean_target, "ffuf", "path", p, "Hidden path discovered")
            return f"--- [DIR] FFUF DISCOVERY REPORT ---\nDiscovered {len(paths)} paths. Top findings:\n" + "\n".join(paths[:40])

        return "FFUF completed. No notable paths found or timeout reached."
