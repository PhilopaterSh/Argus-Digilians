import re

from tools.utils import clean_target


class SecretAnalyzer:
    """Responsible only for secret and PII pattern analysis."""

    PATTERNS = {
        "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "API Key (Generic)": r"(?:key|api|token|secret|auth)[-_=:]+([a-zA-Z0-9]{20,})",
        "Google API Key": r"AIza[0-9A-Za-z-_]{35}",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "S3 Bucket": r"[a-z0-9.-]+\.s3\.amazonaws\.com",
        "Firebase URL": r"[a-z0-9-]+\.firebaseio\.com",
    }

    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory

    def analyze_secrets(self, url: str) -> str:
        print(f"[*] Analyzing for Secrets & PII in: {url}")
        body = self.runner.run(f"curl -s -L {url} | head -c 50000")
        target = clean_target(url)

        found = []
        for name, regex in self.PATTERNS.items():
            matches = re.findall(regex, body, re.IGNORECASE)
            if not matches:
                continue

            unique_matches = list(set(matches))[:5]
            found.append(f"[!] {name}: {', '.join(unique_matches)}")

            for match in unique_matches:
                self.memory.upsert_entity("secret", match, metadata={"category": name})
                self.memory.add_relation(target, match, "EXPOSES")

        if not found:
            return "No obvious secrets or credentials leaked in the landing page HTML."

        return "--- 🔍 LEAKED SECRETS ANALYSIS ---\n" + "\n".join(found)
