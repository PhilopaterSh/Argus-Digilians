import os
from datetime import datetime

class VulnerabilityScanners:
    """Specialized service for running automated scanners like Nikto and FFUF."""

    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory

    def run_nikto(self, url):
        """Runs Nikto vulnerability scanner inside Kali against a web target."""
        print(f"[*] Starting Nikto Vulnerability Scan for: {url}")
        
        output_dir = "reports/nikto"
        os.makedirs(output_dir, exist_ok=True)
        
        clean_target = url.replace("https://", "").replace("http://", "").rstrip('/').replace("/", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"nikto_{clean_target}_{timestamp}.txt"
        output_path = f"{output_dir}/{filename}"
        
        cmd = f"nikto -h {url} -nointeractive -maxtime 120s -Format txt -o {output_path}"
        res = self.runner.run(cmd)

        findings = [l for l in res.split('\n') if l.strip().startswith("+")]
        if findings:
            target_for_mem = url.replace("https://", "").replace("http://", "").split("/")[0]
            for f in findings:
                self.memory.add_finding(target_for_mem, "nikto", "vulnerability", f, "Potential vulnerability detected")

        return f"--- [TOOLS] NIKTO VULNERABILITY REPORT (Saved to {output_path}) ---\n{res}"

    def run_ffuf_discovery(self, url):
        """Runs FFUF for fast directory discovery inside Kali."""
        clean_url = url.rstrip('/')
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"

        print(f"[*] Starting FFUF Path Discovery for: {clean_url}")
        cmd = f"ffuf -w {wordlist} -u {clean_url}/FUZZ -mc 200,301,302 -s -t 50 -maxtime 110"
        res = self.runner.run(cmd)

        if res.strip():
            paths = res.strip().splitlines()
            clean_target = url.replace("https://", "").replace("http://", "").split("/")[0]
            for p in paths[:20]:
                self.memory.add_finding(clean_target, "ffuf", "path", p, "Hidden path discovered")
            return f"--- [DIR] FFUF DISCOVERY REPORT ---\nDiscovered {len(paths)} paths. Top findings:\n" + "\n".join(paths[:40])

        return "FFUF completed. No notable paths found or timeout reached."
