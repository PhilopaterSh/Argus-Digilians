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
        self.runner = runner

    def fuzz_sensitive_files(self, url: str) -> str:
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
        full_url = f"{clean_url}/{path}"
        cmd = f"curl -s -L -I -w '%{{http_code}} %{{size_download}}' -o /dev/null {full_url}"
        result = self.runner.run(cmd).strip()

        if result.startswith(("200", "206")):
            return f"[!] FOUND: {full_url} (Status: {result})"
        if result.startswith("403"):
            return f"[?] PROTECTED: {full_url} (403 Forbidden - Potential Bypass Target)"
        return None
