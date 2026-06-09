from tools.utils import clean_target


class VulnerabilityScanners:
    """Responsible only for scanner integrations like Nikto and FFUF."""

    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory

    def run_nikto(self, url: str) -> str:
        print(f"[*] Starting Nikto Vulnerability Scan for: {url}")
        command = f"nikto -h {url} -nointeractive -maxtime 120s -Format txt"
        result = self.runner.run(command)

        findings = [line for line in result.split("\n") if line.strip().startswith("+")]
        if findings:
            target = clean_target(url)
            for finding in findings:
                self.memory.add_finding(
                    target,
                    "nikto",
                    "vulnerability",
                    finding,
                    "Potential vulnerability detected",
                )

        return f"--- 🛠️ NIKTO VULNERABILITY REPORT ---\n{result}"

    def run_ffuf_discovery(self, url: str) -> str:
        clean_url = url.rstrip("/")
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"

        print(f"[*] Starting FFUF Path Discovery for: {clean_url}")
        command = f"ffuf -w {wordlist} -u {clean_url}/FUZZ -mc 200,301,302,403 -s"
        result = self.runner.run(command)

        if result.strip():
            paths = result.strip().splitlines()
            target = clean_target(url)
            for path in paths[:20]:
                self.memory.add_finding(target, "ffuf", "path", path, "Hidden path discovered")

            return (
                f"--- 📁 FFUF DISCOVERY REPORT ---\n"
                f"Discovered {len(paths)} paths. Top findings:\n"
                + "\n".join(paths[:40])
            )

        return "FFUF completed. No notable paths found."
