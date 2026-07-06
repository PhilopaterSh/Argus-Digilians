import re

class SecretAnalyzer:
    """Analyzes page content and JS files for leaked secrets and credentials."""

    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory

    def analyze_secrets(self, url):
        """Fetches the page body and JS files to look for leaked secrets using Regex."""
        print(f"[*] [Argus-Core] Analyzing secrets for: {url}")
        
        # Regex patterns for common secrets
        patterns = {
            "Generic API Key": r"(?:key|api|token|secret|auth|password)[\"']?\s*[:=]\s*[\"']([a-zA-Z0-9_\-\.]{16,})[\"']",
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Google API Key": r"AIza[0-9A-Za-z\\-_]{35}",
            "Firebase URL": r"https://[a-z0-9-]+\.firebaseio\.com",
            "Slack Webhook": r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+",
            "Environment Variable": r"(?:DB_PASSWORD|DB_USER|STRIPE_KEY|GITHUB_TOKEN)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-\.]{8,})[\"']?"
        }

        # Fetch page content via curl
        page_content = self.runner.run(f"curl -s -L {url} | head -n 500")
        
        found = []
        clean_target = url.replace("https://", "").replace("http://", "").split("/")[0]

        for name, pattern in patterns.items():
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            if matches:
                for m in set(matches):
                    finding = f"[!] Possible {name} Found: {m}"
                    found.append(finding)
                    self.memory.add_finding(clean_target, "secret_analyzer", "leak", name, finding)

        if not found:
            return "No obvious secrets or credentials leaked in the landing page HTML."

        report = "--- [SEARCH] LEAKED SECRETS ANALYSIS ---\n" + "\n".join(found)
        return f"```\n{report}\n```"
