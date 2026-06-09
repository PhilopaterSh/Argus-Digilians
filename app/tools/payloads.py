
class PayloadSuggester:
    """Responsible only for finding local PayloadsAllTheThings entries."""

    MAPPING = {
        "xss": "XSS Injection",
        "sqli": "SQL Injection",
        "nosqli": "NoSQL Injection",
        "ssrf": "Server Side Request Forgery",
        "ssti": "Server Side Template Injection",
        "lfi": "File Inclusion",
        "rfi": "File Inclusion",
        "rce": "Command Injection",
        "cmd": "Command Injection",
        "xxe": "XXE Injection",
        "traversal": "Directory Traversal",
        "csrf": "Cross-Site Request Forgery",
        "jwt": "JSON Web Token",
        "upload": "Upload Insecure Files",
        "api": "API Key Leaks",
        "headers": "Methodology and Resources",
    }

    def __init__(self, runner):
        self.runner = runner

    def suggest_payloads(self, vulnerability_type: str) -> str:
        matched_directory = self._match_directory(vulnerability_type)

        if not matched_directory:
            return (
                f"No specific payloads found for '{vulnerability_type}'. "
                "Suggestion: Search PayloadsAllTheThings manually or check generic methodology."
            )

        print(f"[*] Fetching payloads from: {matched_directory}")
        command = (
            f"cat \"/opt/payloads/PayloadsAllTheThings/{matched_directory}/README.md\" "
            "| grep -A 5 '```' | head -n 30"
        )
        payload_data = self.runner.run(command)

        reflection = f"--- 🛠️ SUGGESTED PAYLOADS/METHODOLOGY FOR {matched_directory} ---\n"
        reflection += payload_data if payload_data else "No sample payloads found in README. Try looking for specific bypass files in that directory."
        reflection += f"\nSource: PayloadsAllTheThings/{matched_directory}"
        return reflection

    def _match_directory(self, vulnerability_type: str):
        vuln_type = vulnerability_type.lower().strip()

        for key, folder in self.MAPPING.items():
            if key in vuln_type:
                return folder

        search_result = self.runner.run(
            f"find /opt/payloads/PayloadsAllTheThings -maxdepth 1 -type d -iname '*{vuln_type}*'"
        ).strip()

        if search_result and "/opt/payloads" in search_result:
            return search_result.split("/")[-1]

        return None
