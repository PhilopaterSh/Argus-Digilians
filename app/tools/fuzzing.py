from concurrent.futures import ThreadPoolExecutor


class SensitiveFileFuzzer:
    """Responsible only for checking sensitive files and common leaks."""

    SENSITIVE_PATHS = [
        ".env",
        ".git/config",
        ".git/index",
        "phpinfo.php",
        "config.php.bak",
        "wp-config.php.save",
        ".htaccess",
        "server-status",
        ".ssh/id_rsa",
        "api/.env",
        "backup.sql",
        "database.sql",
        ".aws/credentials",
        "composer.json",
        "package.json",
        ".npmrc",
    ]

    def __init__(self, runner):
        """Store the shared command runner.

        Args:
            runner: Object with a `run(command)` method that executes a
                shell command (via WSL/SSH) and returns its output as a str.
        """
        self.runner = runner

    def fuzz_sensitive_files(self, url: str) -> str:
        """Probe a fixed list of commonly-exposed sensitive file paths under `url`.

        Args:
            url (str): Target base URL (scheme + host[:port], with or
                without a trailing slash).

        Returns:
            str: A formatted report of found/protected paths, or an
            explicit "no common sensitive files found" message if none of
            `SENSITIVE_PATHS` returned a 2xx/403.
        """
        clean_url = url.rstrip("/")
        print(f"[*] Starting Smart Fuzzing for: {clean_url}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            findings = list(executor.map(lambda p: self._check_path(clean_url, p), self.SENSITIVE_PATHS))

        results = [finding for finding in findings if finding]

        if not results:
            return "No common sensitive files found. Target seems well-configured or using a WAF."

        report = "--- SENSITIVE FILE DISCOVERY REPORT ---\n"
        report += "\n".join(results)
        return report

    def _check_path(self, clean_url: str, path: str):
        """Issue one HEAD-style probe for a single candidate sensitive path.

        Args:
            clean_url (str): Target base URL with no trailing slash.
            path (str): Candidate sensitive path, e.g. ``".env"``.

        Returns:
            str | None: A "[!] FOUND"/"[?] PROTECTED" summary line on a
            2xx/206/403 response, else `None`.
        """
        full_url = f"{clean_url}/{path}"
        cmd = f"curl -s -L -I -w '%{{http_code}} %{{size_download}}' -o /dev/null {full_url}"
        result = self.runner.run(cmd).strip()

        if result.startswith(("200", "206")):
            return f"[!] FOUND: {full_url} (Status: {result})"
        if result.startswith("403"):
            return f"[?] PROTECTED: {full_url} (403 Forbidden - Potential Bypass Target)"
        return None
