# PayloadsAllTheThings ships a dedicated Intruder/ subfolder per category -
# plain, one-payload-per-line wordlists meant for tools like Burp
# Intruder/ffuf, unlike README.md's prose+code-fence mix that
# suggest_payloads() scrapes for human-readable research text. Confirmed
# live against the local mirror in Kali WSL (`wc -l`/`head` on the actual
# files) before wiring this up - dotdotpwn.txt alone has 21k+ real
# traversal payloads including plain "../../../etc/passwd" variants;
# Generic_ErrorBased.txt/Generic_UnionSelect.txt hold real SQLi strings.
# Scoped to just the two vulnerability classes advanced_vuln_probe()
# actually probes (path traversal, SQLi) - suggest_payloads() above already
# covers the other categories as research text, not live-attack payloads.
INTRUDER_WORDLISTS = {
    "path_traversal": ("Directory Traversal", "dotdotpwn.txt"),
    "sqli": ("SQL Injection", "Generic_ErrorBased.txt"),
}


def fetch_intruder_payloads(runner, vulnerability_type, limit=4):
    """Pull a small random sample of real payload strings from the local
    PayloadsAllTheThings mirror's Intruder/ wordlists, to diversify a live
    probe beyond a small hardcoded list.

    Args:
        runner: Object with a `run(command)` method (shared CommandRunner).
        vulnerability_type (str): One of `INTRUDER_WORDLISTS`' keys.
        limit (int): Max payloads to sample - kept small since each one
            becomes a real network probe with its own stealth delay
            (`EvasionService.stealth_run`); this is enrichment on top of an
            existing static list, not a full wordlist fuzz.

    Returns:
        list[str]: Up to `limit` real payload strings, or `[]` (never
        raises) if the vulnerability type isn't mapped, the local mirror
        isn't present, or the wordlist file is missing - callers merge this
        with their own static list, so a missing mirror never regresses
        below what they already try without it.
    """
    mapping = INTRUDER_WORDLISTS.get(vulnerability_type)
    if not mapping:
        return []
    category, filename = mapping
    path = f"/opt/payloads/PayloadsAllTheThings/{category}/Intruder/{filename}"
    raw = runner.run(f"shuf -n {limit} \"{path}\" 2>/dev/null")
    if not raw or "No such file" in raw or "Error" in raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


class PayloadSuggester:
    """Fetches payloads from PayloadsAllTheThings repository in Kali."""

    def __init__(self, runner):
        self.runner = runner

    def suggest_payloads(self, vulnerability_type):
        """Searches PayloadsAllTheThings for relevant payloads based on the vulnerability type."""
        print(f"[*] Fetching suggested payloads for: {vulnerability_type}")

        vt = (vulnerability_type or "").lower()

        # Callers (e.g. brain._build_exploit_query) pass verbose vuln-class
        # phrases like "SQL authentication bypass injection", not the exact
        # short codes an exact-key dict expects. Match on signal words so
        # both a short code ("sqli") and a full phrase resolve to a real
        # PayloadsAllTheThings directory. Order matters: most specific first.
        signal_map = [
            (("sqli", "sql"), "SQL Injection"),
            (("xss", "cross-site script", "cross site script"), "XSS Injection"),
            (("lfi", "rfi", "file inclusion", "traversal"), "File Inclusion"),
            (("ssti", "template injection"), "Server Side Template Injection"),
            (("command injection", "command_injection", "rce"), "Command Injection"),
            (("upload",), "Upload Insecure Files"),
            (("nosql",), "NoSQL Injection"),
            (("graphql",), "GraphQL Injection"),
            # login / auth-bypass endpoints -> SQLi payloads are the right start
            (("auth", "bypass", "login"), "SQL Injection"),
        ]

        matched_dir = next(
            (directory for signals, directory in signal_map if any(s in vt for s in signals)),
            None,
        )
        if not matched_dir:
            return f"No specialized payload repository found for '{vulnerability_type}'. Try searching specifically for 'sqli', 'xss', 'lfi', etc."

        print(f"[*] Fetching payloads from: {matched_dir}")
        cmd = f"cat \"/opt/payloads/PayloadsAllTheThings/{matched_dir}/README.md\" | grep -A 5 -P '\\x60\\x60\\x60' | head -n 30"
        payload_data = self.runner.run(cmd)

        reflection = f"--- [TOOLS] SUGGESTED PAYLOADS/METHODOLOGY FOR {matched_dir} ---\n"
        reflection += "Source: PayloadsAllTheThings (Local Mirror)\n"
        reflection += payload_data
        
        return f"```\n{reflection}\n```"
