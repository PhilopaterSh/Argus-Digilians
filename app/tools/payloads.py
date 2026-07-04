class PayloadSuggester:
    """Fetches payloads from PayloadsAllTheThings repository in Kali."""

    def __init__(self, runner):
        self.runner = runner

    def suggest_payloads(self, vulnerability_type):
        """Searches PayloadsAllTheThings for relevant payloads based on the vulnerability type."""
        print(f"[*] Fetching suggested payloads for: {vulnerability_type}")
        
        mapping = {
            "sqli": "SQL Injection",
            "xss": "XSS Injection",
            "lfi": "File Inclusion",
            "rfi": "File Inclusion",
            "ssti": "Server Side Template Injection",
            "command_injection": "Command Injection",
            "nosql": "NoSQL Injection",
            "graphql": "GraphQL Injection"
        }
        
        matched_dir = mapping.get(vulnerability_type.lower())
        if not matched_dir:
            return f"No specialized payload repository found for '{vulnerability_type}'. Try searching specifically for 'sqli', 'xss', 'lfi', etc."

        print(f"[*] Fetching payloads from: {matched_dir}")
        cmd = f"cat \"/opt/payloads/PayloadsAllTheThings/{matched_dir}/README.md\" | grep -A 5 -P '\\x60\\x60\\x60' | head -n 30"
        payload_data = self.runner.run(cmd)

        reflection = f"--- 🛠️ SUGGESTED PAYLOADS/METHODOLOGY FOR {matched_dir} ---\n"
        reflection += "Source: PayloadsAllTheThings (Local Mirror)\n"
        reflection += payload_data
        
        return f"```\n{reflection}\n```"
