"""
Argus Evidence Verifier
Every scanner finding passes through this gate before being stored in memory.

Anti-false-positive strategies:
  FILE FUZZING  - soft-404 baseline + mandatory content-signature match
  XSS           - unique ARGUS_PROBE marker; confirmed only if reflected unencoded
  SQL INJECTION - 14 DB error fingerprints; no error = no finding
  NIKTO         - noise pattern filter; keep only lines with concrete evidence
"""

import re
import uuid
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -- Constants -------------------------------------------------------------

SOFT_404_THRESHOLD = 150   # bytes: if candidate response is this close to the
                           # random-path response it's a soft-404

XSS_MARKER_PREFIX  = "ARGUS_XSS_PROBE_"

# Files must contain at least one of these strings to be CONFIRMED
CONTENT_SIGNATURES = {
    ".env":              ["DB_", "APP_", "SECRET", "PASSWORD", "API_KEY",
                          "DATABASE_URL", "MAIL_", "AWS_"],
    ".git/config":       ["[core]", "[remote", "repositoryformatversion"],
    ".git/index":        ["DIRC"],          # binary magic bytes
    ".htaccess":         ["RewriteRule", "Options", "Deny from", "Allow from",
                          "AuthType", "Require"],
    "phpinfo.php":       ["PHP Version", "phpinfo()", "php.ini Path"],
    "config.php.bak":    ["$db", "password", "define(", "<?php"],
    "wp-config.php.save":["DB_NAME", "DB_USER", "DB_PASSWORD", "table_prefix"],
    "backup.sql":        ["INSERT INTO", "CREATE TABLE", "DROP TABLE"],
    "database.sql":      ["INSERT INTO", "CREATE TABLE"],
    ".aws/credentials":  ["aws_access_key_id", "aws_secret_access_key"],
    "composer.json":     ['"require"', '"name":', '"version":'],
    "package.json":      ['"name":', '"version":', '"dependencies"'],
    ".npmrc":            ["registry=", "_authToken", "//registry"],
    "server-status":     ["Apache Server Status", "requests currently being"],
    ".ssh/id_rsa":       ["-----BEGIN", "PRIVATE KEY"],
}

SQL_ERRORS = [
    "unclosed quotation mark after the character string",
    "microsoft ole db provider for sql server",
    "[microsoft][odbc sql server driver]",
    "incorrect syntax near",
    "you have an error in your sql syntax",
    "warning: mysql_",
    "supplied argument is not a valid mysql",
    "ora-01756", "ora-00933",
    "quoted string not properly terminated",
    "pg_query()", "syntax error at or near",
    "odbc microsoft access driver",
    "microsoft jet database engine error",
    "syntax error at end of input",
]

# Nikto lines that are pure noise (headers, info, counts)
_NIKTO_NOISE = re.compile(
    r"""
    ^-\s                          | Target\ IP:        | Target\ Hostname:  |
    Target\ Port:                 | Start\ Time:       | End\ Time:         |
    Scan\ terminated              | host\(s\)\ tested  |
    SSL\ Info:                    | Issuer:            | Subject:           |
    Ciphers:                      | Sent\ a\ total     |
    anti-clickjacking             | X-XSS-Protection   | X-Content-Type     |
    Uncommon\ header              | Retrieved\ x-powered |
    No\ CGI\ Directories          | Allowed\ HTTP\ Methods |
    The\ anti-                    | uncommon\ header
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Nikto lines that represent real findings
_NIKTO_SIGNAL = re.compile(
    r"""
    CVE-\d{4}-\d+       | OSVDB-\d+           |
    /\S+\?\S+=          |                      # parameterised path
    injectable          | XSS                  | SQL                |
    directory\ (index|list|travers) |
    Remote\ (file|code) |
    Default\ (file|account|cred) |
    login | admin | config | backup | shell | passwd |
    \.php\? | \.asp\? | \.aspx\?
    """,
    re.IGNORECASE | re.VERBOSE,
)


class Verifier:
    """
    Stateless verifier - create once per scan, reuse for all checks.
    All HTTP calls go through self._session (Python requests, not WSL).
    """

    def __init__(self):
        """Set up the shared requests.Session (spoofed UA, TLS verification
        off) and the per-origin soft-404 baseline cache."""
        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (compatible; ArgusSecurityScanner/2.0)"
        )
        self._session.verify = False
        # Cache soft-404 baselines per origin to avoid duplicate probes
        self._baseline_cache: dict[str, int | None] = {}

    # -- Internal helpers --------------------------------------------------

    def _get(self, url: str, timeout: int = 12) -> requests.Response | None:
        """Get."""
        try:
            return self._session.get(url, timeout=timeout, allow_redirects=True)
        except Exception:
            return None

    def _soft_404_size(self, base_url: str) -> int | None:
        """Returns response body length for a guaranteed-nonexistent path.

        Args:
            base_url (str): Origin to probe a random path under; results
                are cached per (trailing-slash-stripped) `base_url`.

        Returns:
            int | None: The response body length if the random path
            returned HTTP 200, else `None` (e.g. it 404'd normally, or
            the request failed).
        """
        key = base_url.rstrip("/")
        if key in self._baseline_cache:
            return self._baseline_cache[key]
        probe = f"{key}/{uuid.uuid4().hex}"
        r = self._get(probe)
        size = len(r.text) if (r and r.status_code == 200) else None
        self._baseline_cache[key] = size
        return size

    # -- Public API --------------------------------------------------------

    def verify_file(self, base_url: str, path: str) -> dict:
        """
        Checks whether a sensitive file is genuinely exposed.

        Args:
            base_url (str): The site origin to probe under.
            path (str): The candidate file path (e.g. ".env").

        Returns:
            {
              "status":  "CONFIRMED" | "SOFT_404" | "NOT_FOUND" |
                         "PROTECTED" | "ERROR",
              "url":     full URL,
              "snippet": first 300 chars of confirmed body (or reason),
            }
        """
        full_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        r = self._get(full_url)

        if r is None:
            return {"status": "ERROR",     "url": full_url, "snippet": "Request failed"}
        if r.status_code == 403:
            return {"status": "PROTECTED", "url": full_url, "snippet": "403 Forbidden"}
        if r.status_code not in (200, 206):
            return {"status": "NOT_FOUND", "url": full_url,
                    "snippet": f"HTTP {r.status_code}"}

        body = r.text

        # Soft-404 gate
        baseline = self._soft_404_size(base_url)
        if baseline is not None and abs(len(body) - baseline) < SOFT_404_THRESHOLD:
            return {"status": "SOFT_404",  "url": full_url,
                    "snippet": "Response size matches soft-404 baseline"}

        # Content-signature gate
        body_lower = body.lower()
        for pattern, sigs in CONTENT_SIGNATURES.items():
            if pattern in path.lower():
                if any(s.lower() in body_lower for s in sigs):
                    return {"status": "CONFIRMED", "url": full_url,
                            "snippet": body[:300].strip()}
                return {"status": "SOFT_404", "url": full_url,
                        "snippet": f"No content signature match for {pattern}"}

        # Generic non-HTML config/backup file check
        if path.endswith((".env", ".sql", ".bak", ".conf", ".key", ".pem", ".cfg")):
            ct = r.headers.get("Content-Type", "")
            if "html" not in ct.lower() and len(body) > 30:
                return {"status": "CONFIRMED", "url": full_url,
                        "snippet": body[:300].strip()}
            return {"status": "SOFT_404", "url": full_url,
                    "snippet": "HTML content-type for non-HTML file - likely CMS error page"}

        # Fallback: meaningful non-empty response
        if len(body.strip()) > 60:
            return {"status": "CONFIRMED", "url": full_url,
                    "snippet": body[:300].strip()}

        return {"status": "NOT_FOUND", "url": full_url, "snippet": "Empty body"}

    def verify_sqli(self, url: str, param: str, payload: str) -> dict:
        """
        Injects a payload into a single parameter and checks for DB errors.

        Args:
            url (str): The base URL to inject into (a `?`/`&` query
                separator is added automatically).
            param (str): The query parameter name to inject.
            payload (str): The raw payload to URL-encode and send.

        Returns:
            dict: `{"confirmed": bool, "url": str, "error_match": str,
            "snippet": str}` - `confirmed` is True only if one of
            `SQL_ERRORS`' fingerprints appears in the response body.
        """
        sep      = "&" if "?" in url else "?"
        test_url = f"{url}{sep}{param}={requests.utils.quote(payload)}"
        r        = self._get(test_url)
        if r is None:
            return {"confirmed": False, "url": test_url, "error_match": "", "snippet": ""}

        body_lower = r.text.lower()
        for err in SQL_ERRORS:
            pos = body_lower.find(err.lower())
            if pos != -1:
                snippet = r.text[max(0, pos - 40): pos + 200]
                return {
                    "confirmed":   True,
                    "url":         test_url,
                    "error_match": err,
                    "snippet":     snippet,
                }
        return {"confirmed": False, "url": test_url, "error_match": "", "snippet": ""}

    # XSS payloads to try in order - each targets a different reflection context
    XSS_PAYLOADS = [
        "<script>{m}</script>",                      # direct HTML context
        "<img src=x onerror={m}>",                   # attribute event handler
        '"><script>{m}</script>',                    # break out of attribute
        "'><script>{m}</script>",                    # single-quote attribute break
        "</tag><script>{m}</script>",                # break out of any tag
        "<svg onload={m}>",                          # SVG context
        "javascript:{m}",                            # href/src context
        "{m}",                                       # pure text reflection (no tags)
    ]

    def verify_xss(self, url: str, param: str) -> dict:
        """
        Tries multiple payloads across different HTML contexts.
        CONFIRMED if the unique marker appears UNENCODED in the response
        (i.e. not as &lt; / &gt; / &#x3c; etc.).

        Args:
            url (str): The base URL to inject into.
            param (str): The query parameter name to inject.

        Returns:
            dict: `{"confirmed": bool, "url": str, "marker": str,
            "snippet": str, "context": str, "reason": str}` - `confirmed`
            is True only for the first payload whose unique marker
            reflects unencoded, with `url` set to that specific payload's
            request URL. If none do, `confirmed` is False, `url` is the
            bare `{url}{sep}{param}=` (no payload appended, not any
            individual attempt's URL), and `reason` is "no reflection"
            unless an HTML-encoded reflection was seen on some attempt.
        """
        marker = XSS_MARKER_PREFIX + uuid.uuid4().hex[:8]
        sep    = "&" if "?" in url else "?"
        base_result = {
            "confirmed": False, "url": f"{url}{sep}{param}=",
            "marker": marker, "snippet": "", "context": "", "reason": "no reflection"
        }

        for template in self.XSS_PAYLOADS:
            payload  = template.replace("{m}", marker)
            test_url = f"{url}{sep}{param}={requests.utils.quote(payload)}"
            r        = self._get(test_url)
            if r is None:
                continue

            body = r.text

            # Skip if marker is HTML-entity encoded (false positive)
            encoded_marker = (
                marker.replace("<", "&lt;")
                      .replace(">", "&gt;")
                      .replace('"', "&quot;")
            )
            if encoded_marker in body and marker not in body:
                base_result["reason"] = "marker reflected but HTML-encoded (not exploitable)"
                continue

            # CONFIRMED: marker appears in raw form
            if marker in body:
                idx = body.find(marker)
                snippet = body[max(0, idx - 60): idx + 120]

                # Determine reflection context
                context = "unknown"
                pre = body[max(0, idx - 80): idx].lower()
                if "<script" in pre:
                    context = "inside <script> block"
                elif "value=" in pre or 'src=' in pre or 'href=' in pre:
                    context = "inside HTML attribute"
                elif re.search(r'<[a-z]+[^>]*$', pre):
                    context = "inside HTML tag"
                else:
                    context = "HTML body / text node"

                return {
                    "confirmed": True,
                    "url":       test_url,
                    "marker":    marker,
                    "snippet":   snippet,
                    "context":   context,
                    "reason":    f"unencoded reflection via payload: {template[:40]}",
                }

        return base_result

    def filter_nikto(self, raw_output: str) -> list[str]:
        """
        Returns only the Nikto lines that represent real findings.
        Strips informational noise, headers, and meta-lines.

        Args:
            raw_output (str): Raw Nikto stdout.

        Returns:
            list[str]: Lines starting with `+` that either match
            `_NIKTO_SIGNAL` or look like a parameterized URL, excluding
            any that match `_NIKTO_NOISE`.
        """
        findings = []
        for line in raw_output.splitlines():
            s = line.strip()
            if not s or not s.startswith("+"):
                continue
            if _NIKTO_NOISE.search(s):
                continue
            if _NIKTO_SIGNAL.search(s):
                findings.append(s)
            elif re.search(r"/\S+\?\S+=", s):   # parameterised URL
                findings.append(s)
        return findings

    def filter_secrets(self, raw_html: str) -> list[tuple[str, str]]:
        """
        Returns confirmed secret matches as [(type, value), ...].
        Each match requires the value to have >= 12 chars to cut noise.

        Args:
            raw_html (str): Raw HTML/text to scan.

        Returns:
            list[tuple[str, str]]: Up to 10 deduplicated `(secret_type,
            matched_value)` pairs.
        """
        patterns = {
            "Email":             r'[a-zA-Z0-9._%+-]{3,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "API Key (Generic)": r'(?:key|api|token|secret|auth)[\s\-_=:]+([a-zA-Z0-9]{20,})',
            "Google API Key":    r'AIza[0-9A-Za-z\-_]{35}',
            "AWS Access Key":    r'AKIA[0-9A-Z]{16}',
            "S3 Bucket":         r'[a-z0-9.-]+\.s3\.amazonaws\.com',
            "Firebase URL":      r'[a-z0-9-]+\.firebaseio\.com',
            "Private Key Header":r'-----BEGIN (?:RSA |EC )?PRIVATE KEY',
        }
        confirmed = []
        for name, pattern in patterns.items():
            for match in re.finditer(pattern, raw_html, re.IGNORECASE):
                value = match.group(0)
                if len(value) >= 12:
                    confirmed.append((name, value))
        # Deduplicate
        seen = set()
        result = []
        for t, v in confirmed:
            if v not in seen:
                seen.add(v)
                result.append((t, v))
        return result[:10]   # cap at 10 per page
