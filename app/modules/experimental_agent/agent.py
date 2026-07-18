"""
Argus Deterministic Pipeline  (replaces LangChain ReAct agent)

Why deterministic?
  - ReAct agents hallucinate tool calls and invent findings.
  - A fixed pipeline guarantees every step runs, every result is verified,
    and the LLM only summarises confirmed scanner evidence.

Self-healing at every step:
  - Each step is wrapped in _safe_step() which catches all exceptions,
    logs them, and continues - a broken step never aborts the scan.
  - The LLM engine has its own 3-retry + fallback logic.

False-positive reduction:
  - fuzz_sensitive_files  -> Verifier.verify_file() (content-sig + soft-404)
  - XSS checks            -> Verifier.verify_xss() (unique marker, no encoding)
  - SQL injection         -> Verifier.verify_sqli() (14 DB error fingerprints)
  - Nikto output          -> Verifier.filter_nikto() (strip info-only lines)
  - Secrets               -> Verifier.filter_secrets() (min 12-char values)
  - LLM analysis          -> fed ONLY confirmed findings, explicitly told no speculation
"""

import os
import re
import time
import traceback
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.core.memory.memory_service import ArgusMemory
from app.modules.experimental_agent.llm_engine import OllamaEngine
from app.modules.experimental_agent.verifier import Verifier
from app.modules.experimental_agent.agent_payload_decider import AgentPayloadDecider

MODEL    = os.getenv("ARGUS_MODEL", "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest")
TIMEOUT  = 15   # seconds per HTTP probe

# -- Subdomain wordlist (SecLists: Discovery/DNS/subdomains-top1million-5000.txt) --
# Embedded top-300; if local SecLists found, file is loaded at runtime instead.
# -- Directory enumeration wordlist (SecLists: Discovery/Web-Content/common.txt) --
DIRECTORY_WORDLIST = [
    "admin","api","login","logout","dashboard","backup","config","test","dev",
    "staging","data","files","uploads","images","static","assets","css","js",
    "lib","vendor","v1","v2","v3","users","user","account","accounts","profile",
    "settings","panel","manage","management","system","app","public","private",
    "secret","secure","internal","portal","console","cp","administrator","root",
    "temp","tmp","cache","logs","log","debug","shell","cgi-bin","scripts",
    "includes","modules","plugins","themes","templates","install","setup",
    "database","sql","search","ajax","rest","graphql","json","health","status",
    "metrics","analytics","reports","docs","swagger","redoc","openapi","robots.txt",
    "sitemap.xml","phpinfo.php","info.php",".git",".env","wp-admin","wp-login.php",
    "wp-content","wp-includes","xmlrpc.php","phpmyadmin","adminer","webmail",
    "mail","email","smtp","ftp","sftp","ssh","git","svn","jenkins","sonar",
    "jira","confluence","grafana","kibana","prometheus","vault","consul",
    "register","forgot","reset","verify","activate","oauth","auth","token",
    "refresh","logout","signout","signup","signin","authenticate","authorize",
    "upload","download","export","import","migrate","backup2","restore","dump",
    "old","new","beta","alpha","preview","demo","sample","example","test2",
    "api2","api3","v2","v3","v4","internal-api","private-api","hidden",
    "payment","checkout","cart","order","invoice","billing","subscribe",
    "unsubscribe","newsletter","contact","about","help","support","faq","tos",
    "privacy","legal","terms","error","404","500","maintenance","coming-soon",
    "healthcheck","ping","alive","ready","metrics","trace","debug","profiler",
    "console","terminal","exec","run","cmd","shell","rce","eval","boot","init",
]

SUBDOMAIN_WORDLIST = [
    "www","mail","ftp","webmail","smtp","pop","ns1","webdisk","ns2","cpanel",
    "whm","autodiscover","autoconfig","m","imap","test","ns","blog","pop3","dev",
    "www2","admin","forum","news","vpn","ns3","mail2","new","mysql","old","lists",
    "support","mobile","mx","static","docs","beta","shop","sql","secure","demo",
    "cp","calendar","wiki","web","media","email","images","img","www1","intranet",
    "portal","video","sip","api","cdn","stats","dns1","ns4","www3","dns","search",
    "staging","server","mx1","chat","remote","blogs","api2","cdn2","git","smtp2",
    "online","ad","survey","data","mail3","www4","mail1","panel","help","dev2",
    "ns5","cloud","payment","register","files","download","stage","upload","app",
    "apps","store","status","backup","vpn2","assets","auth","login","dashboard",
    "accounts","billing","ticket","helpdesk","kb","sandbox","uat","pre","preprod",
    "prod","internal","corp","extranet","jobs","career","recruit","hr","finance",
    "crm","erp","dev3","qa","qastage","integration","services","service","ws",
    "webservice","api3","api4","graphql","rest","rpc","grpc","microservice","svc",
    "gateway","proxy","lb","loadbalancer","haproxy","nginx","apache","node",
    "jenkins","ci","cd","cicd","build","deploy","devops","monitor","grafana",
    "kibana","elastic","logstash","redis","mongo","mysql","postgres","db","db1",
    "db2","sql1","sql2","oracle","mssql","phpmyadmin","adminer","pgadmin",
    "smtp1","smtp3","imap2","mx2","mx3","relay","bounce","newsletter","mailing",
    "lists2","mailserver","exchange","owa","remote","rdp","vpn1","vpn3","sftp",
    "ssh","bastion","jump","jumpbox","legacy","old2","archive","test2","test3",
    "uat2","staging2","alpha","preview","demo2","sandbox2","beta2","lab","labs",
    "research","blog2","news2","press","media2","images2","cdn3","assets2","files2",
    "download2","upload2","share","drive","storage","backup2","archive2","log",
    "logs","report","reports","analytics","tracking","metrics","prometheus",
    "alertmanager","vault","consul","etcd","k8s","kubernetes","docker","registry",
    "hub","repo","nexus","artifactory","sonar","sonarqube","jira","confluence",
    "wiki2","docs2","help2","support2","ticket2","crm2","erp2","shop2","store2",
    "pay","payment2","checkout","invoice","stripe","paypal","billing2","cart",
    "order","orders","catalog","product","products","api-v1","api-v2","v1","v2",
    "v3","mobile2","app2","ios","android","wap","touch","pwa","staff","hr2",
]

SENSITIVE_FILES = [
    ".env", ".git/config", ".htaccess", "phpinfo.php",
    "config.php.bak", "wp-config.php.save", "backup.sql",
    "database.sql", ".aws/credentials", "composer.json",
    "package.json", ".npmrc", ".ssh/id_rsa", "server-status",
]

SQLI_PAYLOADS = [
    "'", "''", "`", "1' OR '1'='1'--", '1" OR "1"="1"--',
]


class ArgusPipeline:
    """
    Runs an 8-step security scan and returns a full HTML report.

    Usage:
        pipeline = ArgusPipeline(target="https://example.com",
                                 status_cb=print)
        report_html = pipeline.run()
    """

    def __init__(self, target: str, status_cb=None):
        raw = target.strip()

        # -- Detect scan mode from wildcard position ------------------------
        # *.example.com         -> subdomain enumeration
        # example.com/*         -> directory enum at root (1 level)
        # example.com/*/*       -> directory enum 2 levels deep
        # example.com/api/*     -> directory enum inside /api/
        # No star               -> normal single-URL scan

        self._wildcard         = False   # subdomain mode
        self._dir_wildcard     = False   # path/directory mode
        self._dir_segments: list[str] = []  # path segments; '*' marks enum points
        self._base_domain      = ""

        if raw.startswith("*"):
            # Could be:
            #   *.example.com          -> subdomain only
            #   *.example.com/*/*      -> subdomain + directory enum per subdomain
            self._wildcard    = True
            # Strip leading *. to get the rest: "example.com" or "example.com/*/*"
            rest = re.sub(r"^\*\.?", "", raw)   # e.g. "example.com" or "example.com/*/*"

            # Check if there's a path wildcard after the domain
            if "/" in rest and "*" in rest.split("/", 1)[1]:
                # Combined mode: *.example.com/*/*
                domain_part, path_part = rest.split("/", 1)
                self._base_domain  = domain_part          # example.com
                self._dir_wildcard = True
                self._dir_segments = [
                    seg for seg in path_part.split("/") if seg != ""
                ]                                          # ['*', '*']
            else:
                self._base_domain = rest                   # example.com plain
            self.target = f"https://{self._base_domain}"

        elif "*" in raw:
            # Path wildcard: example.com/* or example.com/api/*/*
            self._dir_wildcard = True
            # Normalise: ensure scheme
            if not raw.startswith("http"):
                raw = "https://" + raw
            # Split into base host and path template
            from urllib.parse import urlparse as _urlparse
            _parsed = _urlparse(raw)
            host_part = f"{_parsed.scheme}://{_parsed.netloc}"
            path_part = _parsed.path  # e.g. "/*/*"  or  "/api/*"
            self._dir_base   = host_part          # https://example.com
            self._dir_segments = [
                seg for seg in path_part.split("/") if seg != ""
            ]                                      # e.g. ["*","*"] or ["api","*"]
            self.target = host_part
        else:
            self.target = raw.rstrip("/")

        self.base       = self.target
        self.host       = re.sub(r"https?://", "", self.target).split("/")[0]
        self._cb        = status_cb or (lambda msg, level="info": None)
        self.memory     = ArgusMemory()
        self.llm        = OllamaEngine(model=MODEL)
        self._decider   = AgentPayloadDecider(llm=self.llm, log_cb=self._cb)
        self.verifier   = Verifier()
        self.evidence   = []
        self.step_log   = []
        self._live_subdomains: list[str] = []
        self._found_dirs:      list[str] = []   # populated by dir enum

    # -- Helpers -----------------------------------------------------------

    def _log(self, msg: str, level: str = "info"):
        self._cb(msg, level)
        self.evidence.append(msg)

    def _safe_step(self, name: str, fn, *args, **kwargs):
        """Run fn(*args, **kwargs). On any exception: log, continue, return None."""
        self._log(f"[STEP] {name} ...", "step")
        try:
            result = fn(*args, **kwargs)
            self.step_log.append((name, "ok", ""))
            return result
        except Exception as e:
            detail = traceback.format_exc()
            self._log(f"[!] {name} failed: {e} - skipping", "warn")
            self.step_log.append((name, "error", str(e)))
            return None

    def _http_get(self, url: str):
        try:
            return requests.get(url, timeout=TIMEOUT, verify=False,
                                headers={"User-Agent": "Mozilla/5.0 ArgusScanner/2.0"})
        except Exception:
            return None

    # -- Step 0: Subdomain Enumeration (wildcard mode only) ---------------

    def _load_subdomain_wordlist(self) -> list[str]:
        """
        Try to load a larger wordlist from a local SecLists installation.
        Falls back to the embedded SUBDOMAIN_WORDLIST constant.
        """
        seclists_paths = [
            r"C:\tools\SecLists\Discovery\DNS\subdomains-top1million-5000.txt",
            r"C:\SecLists\Discovery\DNS\subdomains-top1million-5000.txt",
            r"D:\SecLists\Discovery\DNS\subdomains-top1million-5000.txt",
        ]
        for path in seclists_paths:
            if os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8", errors="ignore") as fh:
                        words = [l.strip() for l in fh if l.strip() and not l.startswith("#")]
                    self._log(f"[SubEnum] Loaded {len(words)} entries from local SecLists")
                    return words[:2000]   # cap for performance
                except Exception:
                    pass
        return SUBDOMAIN_WORDLIST

    def _crtsh_subdomains(self, domain: str) -> set[str]:
        """
        Passive: query crt.sh certificate transparency logs.
        Returns a set of subdomain names (without scheme).
        """
        found = set()
        try:
            import json as _json
            r = requests.get(
                f"https://crt.sh/?q=%.{domain}&output=json",
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0 ArgusScanner/2.0"},
            )
            if r.status_code == 200:
                for entry in r.json():
                    for name in entry.get("name_value", "").splitlines():
                        name = name.strip().lstrip("*.")
                        if name.endswith(f".{domain}") and "*" not in name:
                            found.add(name)
                self._log(f"[SubEnum] crt.sh returned {len(found)} unique subdomain(s)")
        except Exception as e:
            self._log(f"[SubEnum] crt.sh failed: {e}", "warn")
        return found

    def _wsl_subfinder(self, domain: str) -> set[str]:
        """Try to run subfinder via WSL - silent if not installed."""
        found = set()
        try:
            import subprocess
            cmd = [
                "wsl", "-d", os.getenv("WSL_DISTRO", "kali-linux"),
                "-u", os.getenv("WSL_USER", "kali"),
                "bash", "-c",
                f"subfinder -d {domain} -silent 2>/dev/null || "
                f"amass enum -passive -d {domain} 2>/dev/null || true",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
                encoding="utf-8", errors="ignore",
            )
            for line in result.stdout.splitlines():
                sub = line.strip()
                if sub.endswith(f".{domain}") and "*" not in sub:
                    found.add(sub)
            if found:
                self._log(f"[SubEnum] WSL tool found {len(found)} subdomain(s)")
        except Exception:
            pass  # WSL / tool not available - skip silently
        return found

    def _httpx_probe(self, hosts: list[str]) -> list[dict]:
        """
        Pass a list of hostnames/URLs to httpx (ProjectDiscovery) via WSL.
        Returns a list of dicts with keys: url, status, title, tech.

        httpx output with -json flag (one JSON object per line):
          {"url":"https://api.example.com","status-code":200,"title":"API","tech":["nginx"]}

        Falls back to Python requests probing if httpx is not installed in WSL.
        """
        import subprocess, json as _json, tempfile

        if not hosts:
            return []

        # Write host list to a temp file accessible by WSL
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp.write("\n".join(hosts))
        tmp.flush()
        tmp.close()

        # Convert Windows path to WSL path
        wsl_path = tmp.name.replace("\\", "/").replace("C:", "/mnt/c").replace("D:", "/mnt/d")

        cmd = [
            "wsl", "-d", os.getenv("WSL_DISTRO", "kali-linux"),
            "-u", os.getenv("WSL_USER", "kali"),
            "bash", "-c",
            f"httpx -l {wsl_path} -silent -status-code -title -tech-detect "
            f"-json -timeout 5 -threads 50 2>/dev/null"
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=120, encoding="utf-8", errors="ignore"
            )
            live = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj  = _json.loads(line)
                    url  = obj.get("url") or obj.get("input", "")
                    code = obj.get("status-code", 0)
                    if url and code and code < 500:
                        live.append({
                            "url":    url,
                            "status": code,
                            "title":  obj.get("title", ""),
                            "tech":   obj.get("tech", []),
                        })
                except _json.JSONDecodeError:
                    pass

            if live:
                self._log(
                    f"[httpx] {len(live)}/{len(hosts)} host(s) live", "step"
                )
                return live

            # httpx returned nothing - either not installed or zero results
            if "command not found" in result.stderr or not result.stdout.strip():
                raise RuntimeError("httpx not found")

        except Exception as e:
            self._log(f"[httpx] Not available ({e}) - falling back to requests", "warn")

        # -- Fallback: Python requests probe -------------------------------
        self._log(f"[httpx-fallback] Probing {len(hosts)} host(s) with requests ...")
        live = []
        for host in hosts:
            for scheme in ("https", "http"):
                url = f"{scheme}://{host}" if not host.startswith("http") else host
                r   = self._http_get(url)
                if r is not None and r.status_code < 500:
                    live.append({
                        "url":    url,
                        "status": r.status_code,
                        "title":  "",
                        "tech":   [],
                    })
                    break
        return live

    def _probe_subdomain(self, subdomain: str) -> str | None:
        """Single-host probe (used when httpx bulk probe is not applicable)."""
        for scheme in ("https", "http"):
            url = f"{scheme}://{subdomain}"
            r = self._http_get(url)
            if r is not None and r.status_code < 500:
                return url
        return None

    def _step_subdomain_enum(self):
        """
        Step 0 - Subdomain Enumeration (runs only when target is *.domain.com)

        Sources (in order):
          1. crt.sh certificate transparency (passive - no brute-force)
          2. DNS brute-force with SecLists wordlist (active - DNS resolution)
          3. WSL subfinder / amass (if installed in WSL)

        Each discovered name is probed for liveness. Live subdomains are
        stored in self._live_subdomains and in memory for the report.
        """
        import socket
        domain = self._base_domain
        self._log(f"[SubEnum] Starting subdomain enumeration for: {domain}", "step")

        # -- Source 1: crt.sh (passive) ------------------------------------
        candidates: set[str] = self._crtsh_subdomains(domain)

        # -- Source 2: DNS brute-force -------------------------------------
        wordlist = self._load_subdomain_wordlist()
        self._log(f"[SubEnum] DNS brute-force with {len(wordlist)} word(s) ...")
        dns_hits = 0
        for word in wordlist:
            sub = f"{word}.{domain}"
            try:
                socket.setdefaulttimeout(2)
                socket.gethostbyname(sub)   # resolves -> exists
                candidates.add(sub)
                dns_hits += 1
            except (socket.gaierror, socket.timeout):
                pass
        self._log(f"[SubEnum] DNS brute-force: {dns_hits} name(s) resolved")

        # -- Source 3: WSL tools -------------------------------------------
        candidates |= self._wsl_subfinder(domain)

        self._log(f"[SubEnum] Total unique candidates: {len(candidates)}")

        # -- Liveness probe via httpx --------------------------------------
        self._log(f"[SubEnum] Passing {len(candidates)} candidate(s) to httpx ...")
        live_results = self._httpx_probe(sorted(candidates))

        for entry in live_results:
            url   = entry["url"]
            code  = entry["status"]
            title = entry["title"]
            tech  = ", ".join(entry["tech"]) if entry["tech"] else ""
            host  = re.sub(r"https?://", "", url).split("/")[0]

            self._live_subdomains.append(url)
            self._log(
                f"  [LIVE] {url}  [{code}]"
                + (f"  \"{title}\"" if title else "")
                + (f"  tech={tech}" if tech else ""),
                "high"
            )
            self.memory.upsert_target(host)
            self.memory.add_finding(
                host, "subdomain_enum", "path",
                f"httpx confirmed live: {url}\nStatus: {code}\n"
                f"Title: {title}\nTech: {tech}",
                f"Live subdomain: {host} [{code}]"
                + (f" - {title}" if title else ""),
                severity="Medium",
            )

        self._log(
            f"[SubEnum] {len(self._live_subdomains)} live subdomain(s) found - "
            "scanning each now ...", "step"
        )

    def _scan_subdomain(self, sub_url: str):
        """
        Run a focused scan on a single discovered subdomain.
        Covers: fingerprint, file fuzz, secrets, XSS, SQLi.
        Nikto and Think_And_Adapt are skipped per-subdomain for speed;
        they run once over all findings at the end.
        """
        sub_host = re.sub(r"https?://", "", sub_url).split("/")[0]
        self._log(f"\n{'-'*60}", "step")
        self._log(f"[Scan] {sub_url}", "step")

        # Swap to subdomain context
        orig_target, orig_base, orig_host = self.target, self.base, self.host
        self.target = sub_url
        self.base   = sub_url
        self.host   = sub_host

        self._safe_step(f"Fingerprint:{sub_host}",    self._step_fingerprint)
        self._safe_step(f"Header_Security:{sub_host}", self._step_header_security)
        self._safe_step(f"File_Fuzz:{sub_host}",    self._step_fuzz_files)
        self._safe_step(f"Secrets:{sub_host}",      self._step_secrets)
        self._safe_step(f"SQLi:{sub_host}",         self._step_sqli)
        self._safe_step(f"XSS:{sub_host}",          self._step_xss)

        # Restore original context
        self.target = orig_target
        self.base   = orig_base
        self.host   = orig_host

    # -- Directory enumeration (path wildcard mode) -----------------------

    def _load_dir_wordlist(self) -> list[str]:
        """Try local SecLists first, fall back to embedded list."""
        paths = [
            r"C:\tools\SecLists\Discovery\Web-Content\common.txt",
            r"C:\SecLists\Discovery\Web-Content\common.txt",
            r"D:\SecLists\Discovery\Web-Content\common.txt",
            r"C:\tools\SecLists\Discovery\Web-Content\directory-list-2.3-small.txt",
        ]
        for p in paths:
            if os.path.isfile(p):
                try:
                    with open(p, encoding="utf-8", errors="ignore") as fh:
                        words = [
                            l.strip() for l in fh
                            if l.strip() and not l.startswith("#")
                        ]
                    self._log(f"[DirEnum] Loaded {len(words)} entries from local SecLists")
                    return words[:3000]
                except Exception:
                    pass
        return DIRECTORY_WORDLIST

    def _probe_path(self, url: str) -> bool:
        """Return True if the path exists (2xx/3xx, not a soft-404)."""
        dir_base = getattr(self, "_dir_base", self.target)
        baseline_url = dir_base + "/__argus_nonexistent_probe__"
        br = self._http_get(baseline_url)
        baseline_len = len(br.text) if br and br.status_code == 200 else None

        r = self._http_get(url)
        if r is None:
            return False
        if r.status_code in (404, 410):
            return False
        if r.status_code == 200 and baseline_len is not None:
            # Soft-404 check: if response is same size as baseline -> fake 200
            if abs(len(r.text) - baseline_len) < 150:
                return False
        return r.status_code < 400 or r.status_code in (401, 403)

    def _enumerate_level(self, base_path: str, wordlist: list[str]) -> list[str]:
        """
        Enumerate one directory level under base_path.
        Builds the full candidate URL list, then passes them ALL to httpx
        in one bulk call - much faster than probing one-by-one.
        Returns list of confirmed live URLs.
        """
        dir_base  = getattr(self, "_dir_base", self.target)
        base_path = base_path.rstrip("/")
        self._log(
            f"[DirEnum] Fuzzing: {dir_base}{base_path}/ "
            f"({len(wordlist)} words) via httpx"
        )

        # Build all candidate URLs
        candidates = [f"{dir_base}{base_path}/{word}" for word in wordlist]

        # Bulk httpx probe
        live_results = self._httpx_probe(candidates)

        found = []
        for entry in live_results:
            url  = entry["url"]
            code = entry["status"]
            # Exclude obvious soft-404s (401/403 are valid - auth-protected = interesting)
            self._log(f"  [FOUND] [{code}] {url}", "high")
            found.append(url)
            self.memory.add_finding(
                self.host, "dir_enum", "path",
                f"GET {url}\nHTTP {code}\nTitle: {entry.get('title','')}\n"
                f"Tech: {', '.join(entry.get('tech',[]))}",
                f"Directory/path found [{code}]: {url}",
                severity="Medium",
            )
        return found

    def _step_dir_enum(self):
        """
        Path wildcard directory enumeration.

        Parses self._dir_segments - each segment is either:
          - a literal string  -> fixed path component (e.g. 'api')
          - '*'               -> enumerate at this level

        Examples:
          ['*']           ->  enumerate root  (/admin, /api, ...)
          ['*', '*']      ->  enumerate root, then enumerate each result 1 level deeper
          ['api', '*']    ->  enumerate /api/ only
          ['*', 'admin']  ->  enumerate root, check /FOUND/admin on each
        """
        wordlist = self._load_dir_wordlist()
        segments = self._dir_segments   # e.g. ['*', '*'] or ['api', '*']

        # Build starting paths by walking the segments left-to-right
        # current_paths = list of (url_path_string, remaining_segments)
        current_paths: list[tuple[str, list[str]]] = [("/", list(segments))]
        all_found: list[str] = []

        while current_paths:
            next_paths: list[tuple[str, list[str]]] = []
            for base_path, remaining in current_paths:
                if not remaining:
                    continue
                seg = remaining[0]
                rest = remaining[1:]

                if seg == "*":
                    # Enumerate this level
                    found_urls = self._enumerate_level(base_path, wordlist)
                    all_found.extend(found_urls)
                    if rest:
                        # More segments after this star -> continue with each found dir
                        for furl in found_urls:
                            # Extract just the path portion
                            fpath = furl.replace(self._dir_base, "")
                            next_paths.append((fpath, list(rest)))
                else:
                    # Fixed segment - build path and continue
                    new_path = base_path.rstrip("/") + "/" + seg
                    # Check if this fixed path exists
                    full_url = self._dir_base + new_path
                    if rest:
                        next_paths.append((new_path, list(rest)))
                    else:
                        if self._probe_path(full_url):
                            r = self._http_get(full_url)
                            code = r.status_code if r else "?"
                            self._log(f"  [FOUND] [{code}] {full_url}", "high")
                            all_found.append(full_url)
                            self.memory.add_finding(
                                self.host, "dir_enum", "path",
                                f"GET {full_url}\nHTTP {code}",
                                f"Path found: {full_url}",
                                severity="Medium",
                            )

            current_paths = next_paths

        self._found_dirs = all_found
        self._log(
            f"[DirEnum] Complete - {len(all_found)} path(s) confirmed", "step"
        )

        # Run XSS + SQLi on each found path (they may have parameters)
        for url in all_found[:20]:
            sub_host = re.sub(r"https?://", "", url).split("/")[0]
            orig_target, orig_base, orig_host = self.target, self.base, self.host
            self.target = url
            self.base   = url
            self.host   = sub_host
            self._safe_step(f"XSS:{url[-40:]}", self._step_xss)
            self._safe_step(f"SQLi:{url[-40:]}", self._step_sqli)
            self.target, self.base, self.host = orig_target, orig_base, orig_host

    # -- Step 1: Reachability ----------------------------------------------

    def _step_reachability(self):
        self._log(f"Probing {self.target} ...")
        r = self._http_get(self.target)
        if r is None:
            self._log(f"[FAIL] {self.target} is not reachable", "error")
            return False
        self._log(f"[OK] Reachable - HTTP {r.status_code} "
                  f"Server: {r.headers.get('Server','?')}")
        self.memory.add_finding(
            self.host, "reachability", "headers",
            f"HTTP {r.status_code}\n" + "\n".join(
                f"{k}: {v}" for k, v in list(r.headers.items())[:20]
            ),
            f"HTTP {r.status_code} - Server: {r.headers.get('Server','?')}",
            severity="Info",
        )
        return True

    # -- Step 2: Technology fingerprint -----------------------------------

    def _step_fingerprint(self):
        r = self._http_get(self.target)
        if r is None:
            return
        headers       = dict(r.headers)
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        body          = r.text[:8000]
        body_lower    = body.lower()
        tech_clues    = []
        waf_clues     = []

        # -- Server / powered-by headers ----------------------------------
        for h in ("Server", "X-Powered-By", "X-Generator", "X-AspNet-Version"):
            if h in headers:
                tech_clues.append(f"{h}: {headers[h]}")

        # -- Body: CMS / framework signatures -----------------------------
        body_sigs = {
            "WordPress":         "wp-content",
            "Joomla":            "joomla",
            "Drupal":            "drupal",
            "Laravel":           "laravel",
            "ASP.NET":           "asp.net",
            "React":             "react",
            "Angular":           "__ng_",
            "Vue.js":            "vue.js",
            # Extended v2.0
            "Django":            "csrfmiddlewaretoken",
            "Flask/Werkzeug":    "werkzeug",
            "Spring (Java)":     "whitelabel error page",
            "Ruby on Rails":     "_rails_session",
            "Next.js":           "__next",
            "Symfony":           "sf_redirect",
            "Nuxt.js":           "__nuxt",
        }
        for name, sig in body_sigs.items():
            if sig in body_lower:
                tech_clues.append(f"CMS/Framework: {name}")

        # -- Header: framework leakage -------------------------------------
        xpb = headers_lower.get("x-powered-by", "")
        if "express" in xpb:
            tech_clues.append("CMS/Framework: Express.js (via X-Powered-By)")
        if "php" in xpb:
            tech_clues.append(
                f"Language: PHP (X-Powered-By: {headers.get('X-Powered-By','')})"
            )

        # -- WAF detection: response headers ------------------------------
        waf_header_sigs = {
            "Cloudflare":    "cf-ray",
            "Akamai":        "x-check-cacheable",
            "Sucuri":        "x-sucuri-id",
            "F5 BIG-IP ASM": "x-wa-info",
            "AWS WAF":       "x-amzn-requestid",
            "Imperva":       "x-iinfo",
            "Barracuda":     "bwsa",
        }
        for waf_name, hdr in waf_header_sigs.items():
            if hdr in headers_lower:
                waf_clues.append(f"WAF: {waf_name} (header: {hdr})")

        # -- WAF detection: response body patterns -------------------------
        waf_body_sigs = {
            "ModSecurity":  "mod_security",
            "Cloudflare":   "cloudflare ray id",
            "Sucuri":       "sucuri website firewall",
            "Barracuda":    "barracuda networks",
            "F5 BIG-IP":    "the requested url was rejected",
        }
        for waf_name, sig in waf_body_sigs.items():
            if sig in body_lower:
                if not any(waf_name.split()[0].lower() in c.lower() for c in waf_clues):
                    waf_clues.append(f"WAF: {waf_name} (body pattern)")

        all_clues = tech_clues + waf_clues
        summary   = " | ".join(all_clues) or "Tech stack unclear"
        self._log(f"[Fingerprint] {summary}")
        self.memory.add_finding(
            self.host, "fingerprint", "tech",
            "\n".join(all_clues) + "\n\nHeaders:\n" + str(headers)[:800],
            summary, severity="Info",
        )

    # -- Step 2b: Security header audit -----------------------------------

    def _step_header_security(self):
        """
        Check for missing HTTP security headers.
        Uses a fresh request so this step is independent of fingerprint.
        Severity mapping:
          Content-Security-Policy    -> Critical (XSS amplifier if absent)
          X-Frame-Options            -> Medium   (clickjacking)
          Strict-Transport-Security  -> Medium   (MITM on HTTPS)
          X-Content-Type-Options     -> Low      (MIME-sniffing)
          Referrer-Policy            -> Low      (info-leak)
          Permissions-Policy         -> Low      (browser API surface)
        """
        r = self._http_get(self.target)
        if r is None:
            return
        headers_lower = {k.lower(): v for k, v in r.headers.items()}

        checks = [
            ("content-security-policy",   "Content-Security-Policy",  "Critical"),
            ("x-frame-options",           "X-Frame-Options",           "Medium"),
            ("strict-transport-security", "Strict-Transport-Security", "Medium"),
            # Low-severity headers omitted - excluded from report per scope policy:
            # ("x-content-type-options", "X-Content-Type-Options", "Low"),
            # ("referrer-policy",        "Referrer-Policy",        "Low"),
            # ("permissions-policy",     "Permissions-Policy",     "Low"),
        ]

        missing = []
        present = []
        for hdr_key, hdr_display, severity in checks:
            if hdr_key in headers_lower:
                present.append(f"{hdr_display}: {headers_lower[hdr_key]}")
            else:
                missing.append((hdr_display, severity))

        if not missing:
            self._log("[HeaderSec] All security headers present")
            return

        for hdr_display, severity in missing:
            self._log(f"[HeaderSec] MISSING {hdr_display} ({severity})", "warn")
            self.memory.add_finding(
                self.host, "header_security", "vulnerability",
                f"Missing HTTP security header: {hdr_display}\n"
                f"Target: {self.target}\n"
                f"Present headers: {', '.join(present) or 'none of the checked set'}",
                f"Missing security header: {hdr_display}",
                severity=severity,
            )

    # -- Step 3: Sensitive file discovery (verified) -----------------------

    def _step_fuzz_files(self):
        confirmed = 0
        for path in SENSITIVE_FILES:
            result = self.verifier.verify_file(self.base, path)
            status = result["status"]
            url    = result["url"]
            snippet= result["snippet"]

            if status == "CONFIRMED":
                self._log(f"[CONFIRMED] Sensitive file: {url}", "high")
                ai_payload = self.llm.generate_poc_payload(
                    'leak', path, '', snippet, url
                )
                raw = f"GET {url}\nHTTP 200 OK\nAI_PAYLOAD: {ai_payload}\n\n{snippet}"
                self.memory.add_finding(
                    self.host, "fuzzer", "leak", raw,
                    f"Sensitive file exposed: {path}",
                    severity="High",
                )
                confirmed += 1
            elif status == "PROTECTED":
                self._log(f"[PROTECTED] {url} (403 - potential bypass target)")
                self.memory.add_finding(
                    self.host, "fuzzer", "path",
                    f"GET {url}\nHTTP 403 Forbidden",
                    f"Access-restricted path: {path}",
                    severity="Medium",
                )
            else:
                self._log(f"  [-] {path}: {status}")

        self._log(f"[Fuzz] {confirmed} confirmed file(s) exposed")

    # -- Step 4: Secrets in page source -----------------------------------

    def _step_secrets(self):
        r = self._http_get(self.target)
        if r is None:
            return
        matches = self.verifier.filter_secrets(r.text)
        if matches:
            for kind, value in matches:
                self._log(f"[SECRET] {kind}: {value[:60]}", "critical")
                self.memory.add_finding(
                    self.host, "secrets_scanner", "secrets",
                    f"Found in {self.target}:\n{kind}: {value}",
                    f"{kind} exposed in page source",
                    severity="Critical",
                )
        else:
            self._log("[Secrets] No secrets found in page source")

    # -- Step 5: SQL injection (verified) ---------------------------------

    def _step_sqli(self):
        # Discover parameters from page links
        r = self._http_get(self.target)
        if r is None:
            return
        params_found = re.findall(r'[?&]([a-zA-Z_][a-zA-Z0-9_]*)=', r.text)
        params_found = list(dict.fromkeys(params_found))[:8]  # unique, cap at 8

        # Also test well-known vulnerable ASP endpoints
        fixed_targets = [
            (f"{self.base}/listproducts.asp", "cat"),
            (f"{self.base}/showthread.asp", "id"),
            (f"{self.base}/read.asp", "id"),
        ]
        test_targets = [(self.base, p) for p in params_found] + fixed_targets

        confirmed = 0
        ctx           = self._build_decider_context("sqli")
        sqli_payloads = self._decider.select_payloads(ctx).payloads
        for url, param in test_targets:
            for payload in sqli_payloads:
                res = self.verifier.verify_sqli(url, param, payload)
                if res["confirmed"]:
                    self._log(
                        f"[CONFIRMED SQLi] {url}?{param}= "
                        f"payload={payload!r} match={res['error_match']!r}", "critical"
                    )
                    ai_payload = self.llm.generate_poc_payload(
                        'sqli', param,
                        f"DB error: {res['error_match']}",
                        res['snippet'], res['url']
                    )
                    self.memory.add_finding(
                        self.host, "sqli_scanner", "sqli",
                        f"URL: {res['url']}\nParam: {param}\nPayload: {payload}\n"
                        f"DB Error: {res['error_match']}\nAI_PAYLOAD: {ai_payload}\n\n{res['snippet']}",
                        f"SQL Injection confirmed - param '{param}', error: {res['error_match']}",
                        severity="Critical",
                    )
                    confirmed += 1
                    break   # one confirmed payload per param is enough
        self._log(f"[SQLi] {confirmed} confirmed injection point(s)")

    # -- Step 6: XSS detection (verified) ---------------------------------

    def _collect_xss_targets(self, r) -> list[tuple[str, str]]:
        """
        Build a list of (test_url, param_name) pairs from multiple sources:
          1. Params already in the target URL itself  (?search=test)
          2. <form> action + <input name=...> fields
          3. ?param= patterns found in page links / text
        Returns unique (url, param) pairs, capped at 15.
        """
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        targets: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()

        def add(url: str, param: str):
            key = (url.split("?")[0], param)
            if key not in seen:
                seen.add(key)
                targets.append((url.split("?")[0], param))

        # 1. Params in the target URL itself
        parsed = urlparse(self.target)
        for param in parse_qs(parsed.query):
            base_no_qs = urlunparse(parsed._replace(query=""))
            add(base_no_qs, param)

        if r is None:
            return targets[:15]

        body = r.text

        # 2. <form> inputs - extract action + all input/textarea names
        form_actions = re.findall(r'<form[^>]*action=["\']([^"\']*)["\']', body, re.I)
        input_names  = re.findall(r'<input[^>]*name=["\']([^"\']+)["\']', body, re.I)
        input_names += re.findall(r'<textarea[^>]*name=["\']([^"\']+)["\']', body, re.I)
        form_base = (
            form_actions[0] if form_actions else self.base
        )
        if not form_base.startswith("http"):
            form_base = self.base.rstrip("/") + "/" + form_base.lstrip("/")
        for name in input_names:
            if name.lower() not in ("submit", "csrf", "_token", "hidden"):
                add(form_base, name)

        # 3. ?param= patterns in page body (links, js, etc.)
        for param in re.findall(r'[?&]([a-zA-Z_][a-zA-Z0-9_]*)=', body):
            add(self.base, param)

        # 4. Common generic param names always worth trying
        for param in ("q", "search", "query", "s", "id", "name",
                      "input", "keyword", "term", "text", "url", "redirect"):
            add(self.base, param)

        return targets[:15]

    def _step_xss(self):
        r = self._http_get(self.target)
        # Don't abort if page fails - we still have URL params
        test_targets = self._collect_xss_targets(r)

        if not test_targets:
            self._log("[XSS] No parameters found to test")
            return

        self._log(f"[XSS] Testing {len(test_targets)} parameter(s) ...")
        confirmed = 0
        for url, param in test_targets:
            res = self.verifier.verify_xss(url, param)
            if res["confirmed"]:
                self._log(
                    f"[CONFIRMED XSS] {url}?{param}= "
                    f"marker={res['marker']} ctx={res.get('context','?')}", "high"
                )
                ai_payload = self.llm.generate_poc_payload(
                    'xss', param,
                    res.get('context', ''),
                    res['snippet'], res['url']
                )
                self.memory.add_finding(
                    self.host, "xss_scanner", "xss",
                    f"URL: {res['url']}\nParam: {param}\nMarker: {res['marker']}\n"
                    f"Context: {res.get('context','?')}\nAI_PAYLOAD: {ai_payload}\n\n{res['snippet']}",
                    f"Reflected XSS confirmed - param '{param}' at {url}",
                    severity="High",
                )
                confirmed += 1
            else:
                self._log(f"  [-] {param}: {res.get('reason','no reflection')}")
        self._log(f"[XSS] {confirmed} confirmed injection point(s)")

    # -- Helpers for redirect-sensitive requests ---------------------------

    def _session_get_no_redirect(self, url: str, timeout: int = 12):
        """GET without following redirects; returns Response or None."""
        try:
            return self._session.get(
                url, timeout=timeout,
                allow_redirects=False,
                verify=False,
            )
        except Exception:
            return None

    # -- Step 6a: SSRF detection -------------------------------------------

    def _step_ssrf(self):
        """
        Inject SSRF payloads into URL parameters.
        Detection: response body contains cloud-metadata / loopback service markers.
        """
        from app.modules.experimental_agent.llm_engine import SECLISTS_EMBEDDED
        payloads = SECLISTS_EMBEDDED.get("ssrf", [])[:8]
        if not payloads:
            return

        # SSRF-prone parameter names to try
        ssrf_params = ["url", "path", "src", "dest", "uri",
                       "host", "endpoint", "callback", "redirect", "target"]

        # Build a base param map from the target URL
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed    = urlparse(self.target)
        existing  = parse_qs(parsed.query, keep_blank_values=True)
        # Params to actually probe: existing ones first, then SSRF-prone names
        probe_params = list(existing.keys()) or ssrf_params[:4]

        # Indicators that the SSRF payload was fetched server-side
        ssrf_indicators = [
            "ami-id", "instance-id", "iam/security-credentials",
            "169.254.169.254", "root:x:", "bin:x:", "+PONG",
            "SSH-", "redis_version", "localhost",
        ]

        found = False
        for param in probe_params[:3]:          # limit to 3 params for speed
            for payload in payloads[:5]:         # limit to 5 payloads
                q = dict(existing)
                q[param] = [payload]
                test_url = urlunparse(parsed._replace(
                    query=urlencode(q, doseq=True)
                ))
                r = self._http_get(test_url)
                if r is None:
                    continue
                body_lower = r.text.lower()
                hit = next(
                    (ind for ind in ssrf_indicators if ind.lower() in body_lower),
                    None,
                )
                if hit:
                    self._log(
                        f"[SSRF] Possible SSRF - param={param}, "
                        f"payload={payload[:40]}, indicator={hit}", "high"
                    )
                    ai_payload = self.llm.generate_poc_payload(
                        "ssrf", param, payload, r.text[:300], test_url
                    )
                    self.memory.add_finding(
                        self.host, "ssrf_scanner", "vulnerability",
                        f"GET {test_url}\nIndicator: {hit}\n"
                        f"AI_PAYLOAD: {ai_payload}\n\nSnippet:\n{r.text[:400]}",
                        f"Possible SSRF via param '{param}' - indicator: {hit}",
                        severity="High",
                    )
                    found = True
                    break   # one confirmed finding per param is enough
            if found:
                break

        if not found:
            self._log("[SSRF] No SSRF indicators detected")

    # -- Step 6b: Open Redirect detection ---------------------------------

    def _step_open_redirect(self):
        """
        Inject open-redirect payloads into URL parameters.
        Detection: 3xx Location header points outside the target origin.
        """
        from app.modules.experimental_agent.llm_engine import SECLISTS_EMBEDDED
        payloads = SECLISTS_EMBEDDED.get("open_redirect", [])
        if not payloads:
            return

        redirect_params = ["redirect", "url", "next", "return",
                           "goto", "dest", "rurl", "continue", "destination"]

        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed   = urlparse(self.target)
        existing = parse_qs(parsed.query, keep_blank_values=True)
        probe_params = list(existing.keys()) or redirect_params[:4]

        found = False
        for param in probe_params[:3]:
            for payload in payloads:
                q = dict(existing)
                q[param] = [payload]
                test_url = urlunparse(parsed._replace(
                    query=urlencode(q, doseq=True)
                ))
                r = self._session_get_no_redirect(test_url)
                if r is None:
                    continue
                if r.status_code in (301, 302, 303, 307, 308):
                    location = r.headers.get("Location", "")
                    # Confirm redirect goes outside the target host
                    if location and parsed.netloc.lower() not in location.lower():
                        self._log(
                            f"[OpenRedirect] Confirmed - param={param}, "
                            f"Location: {location}", "high"
                        )
                        ai_payload = self.llm.generate_poc_payload(
                            "open_redirect", param, payload,
                            f"Location: {location}", test_url
                        )
                        self.memory.add_finding(
                            self.host, "redirect_scanner", "vulnerability",
                            f"GET {test_url}\nHTTP {r.status_code}\n"
                            f"Location: {location}\n"
                            f"AI_PAYLOAD: {ai_payload}",
                            f"Open Redirect via param '{param}' -> {location[:80]}",
                            severity="Medium",
                        )
                        found = True
                        break
            if found:
                break

        if not found:
            self._log("[OpenRedirect] No open redirect confirmed")

    # -- Step 6c: XXE detection --------------------------------------------

    def _step_xxe(self):
        """
        POST XXE payloads to target with XML content-type.
        Detection: response body contains file-read indicators (/etc/passwd content).
        """
        from app.modules.experimental_agent.llm_engine import SECLISTS_EMBEDDED
        payloads = SECLISTS_EMBEDDED.get("xxe", [])
        if not payloads:
            return

        xxe_indicators = ["root:x:", "bin:x:", "daemon:x:", "/bin/bash",
                          "/bin/sh", "no such file"]

        found = False
        for payload in payloads:
            try:
                r = self._session.post(
                    self.target,
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/xml"},
                    timeout=TIMEOUT,
                    verify=False,
                )
            except Exception:
                continue

            body_lower = r.text.lower()
            hit = next(
                (ind for ind in xxe_indicators if ind.lower() in body_lower),
                None,
            )
            if hit:
                self._log(
                    f"[XXE] Confirmed XXE - indicator: {hit}", "high"
                )
                ai_payload = self.llm.generate_poc_payload(
                    "xxe", "body", payload, r.text[:300], self.target
                )
                self.memory.add_finding(
                    self.host, "xxe_scanner", "vulnerability",
                    f"POST {self.target}\nContent-Type: application/xml\n"
                    f"Payload: {payload[:200]}\n"
                    f"Indicator: {hit}\n"
                    f"AI_PAYLOAD: {ai_payload}\n\nSnippet:\n{r.text[:400]}",
                    f"XXE Injection confirmed - indicator: {hit}",
                    severity="Critical",
                )
                found = True
                break

        if not found:
            self._log("[XXE] No XXE indicators detected")

    # -- Step 7: Nikto (noise-filtered) -----------------------------------

    def _step_nikto(self):
        """Run Nikto via WSL; filter noise; store only signal lines."""
        try:
            import subprocess
            cmd = [
                "wsl", "-d", os.getenv("WSL_DISTRO", "kali-linux"),
                "-u", os.getenv("WSL_USER", "kali"),
                "bash", "-c",
                f"nikto -h {self.target} -nointeractive -maxtime 90s -Format txt"
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
                encoding="utf-8", errors="ignore"
            )
            raw = result.stdout or result.stderr
            findings = self.verifier.filter_nikto(raw)
            if findings:
                self._log(f"[Nikto] {len(findings)} signal finding(s)")
                for line in findings:
                    self._log(f"  {line}")
                    self.memory.add_finding(
                        self.host, "nikto", "vulnerability",
                        line,
                        line[:120],
                        severity="High",
                    )
            else:
                self._log("[Nikto] No high-signal findings (noise filtered)")
        except Exception as e:
            self._log(f"[Nikto] Skipped: {e}", "warn")

    # -- Self-healing reasoning loop ---------------------------------------


    # -- Agent payload context builder -----------------------------------------

    def _build_decider_context(self, step: str) -> dict:
        """
        Assembles the context dict for AgentPayloadDecider.select_payloads().

        Reads fingerprint findings from this session to extract the detected
        tech stack and WAF name, then bundles everything the decider needs:
        step name, target URL, host, tech stack, WAF, prior findings, and the
        SecLists payload pool for the requested step.

        Called immediately before _step_sqli() executes its payload loop.
        """
        from app.modules.experimental_agent.llm_engine import SECLISTS_EMBEDDED

        findings = self.memory.get_detailed_findings(self.host, since=self._scan_start)

        # Extract tech stack and WAF from the fingerprint step summary.
        # Summary format (from _step_fingerprint):
        #   "Server: nginx | CMS/Framework: WordPress | WAF: Cloudflare (header: cf-ray)"
        tech_stack:   list[str]      = []
        waf_detected: str | None     = None

        for f in findings:
            if f.get("tool_name") == "fingerprint" and f.get("data_type") == "tech":
                for part in f.get("summary", "").split(" | "):
                    part = part.strip()
                    if part.startswith("WAF:"):
                        waf_detected = part[4:].strip().split("(")[0].strip()
                    elif part.startswith("CMS/Framework:"):
                        tech_stack.append(part[14:].strip())
                    elif part.startswith("Server:"):
                        tech_stack.append(part[7:].strip())
                    elif part.startswith("Language:"):
                        tech_stack.append(part[9:].strip())

        return {
            "step":               step,
            "target_url":         self.target,
            "host":               self.host,
            "tech_stack":         tech_stack,
            "waf_detected":       waf_detected,
            "findings_so_far":    findings,
            "available_payloads": SECLISTS_EMBEDDED.get(step, []),
        }


    def _think_and_adapt(self):
        """
        After all scan steps complete, WhiteRabbitNeo reviews the step log,
        identifies failures / zero-result steps, reasons about WHY they failed,
        and autonomously decides whether to re-run them with a dif
        This is the 'think and solve every problem automatically' layer.
        """
        # Build a step report for the LLM
        step_report = '\n'.join(
            f"  [{status.upper()}] {name}: {detail or 'OK'}"
            for name, status, detail in self.step_log
        )
        findings_so_far = self.memory.get_detailed_findings(
            self.host, since=self._scan_start
        )
        finding_count = len(findings_so_far)

        prompt = f"""You are an autonomous penetration testing AI.

A scan of {self.host} has just completed. Below is the step execution log
and a count of confirmed findings so far.

STEP LOG:
{step_report}

CONFIRMED FINDINGS SO FAR: {finding_count}

Your job: review any steps that FAILED or returned zero results.
For each such step, reason about WHY it may have failed and decide
whether to retry it with a different approach.

Respond ONLY with a JSON array of retry objects. Each object must have:
  "step": one of ["xss", "sqli_blind", "file_fuzz"]
  "reason": one sentence explaining why you think it failed
  "params": object with step-specific settings

Example:
[
  {{"step": "xss", "reason": "Initial XSS missed DOM-based sinks", "params": {{"aggressive": true}}}},
  {{"step": "file_fuzz", "reason": "Missed backup extensions", "params": {{"extra_exts": [".bak",".old"]}}}}
]

If no retries are needed, respond with: []
"""

        self._log("[Think] WhiteRabbitNeo reviewing scan results ...")
        raw, _ = self.llm.generate(prompt, temperature=0.1, max_tokens=600)

        # Parse JSON retry list
        try:
            # Extract JSON array from response
            m = __import__('re').search(r'\[.*\]', raw, __import__('re').DOTALL)
            retries = __import__('json').loads(m.group(0)) if m else []
        except Exception:
            retries = []

        if not retries:
            self._log("[Think] No adaptive retries recommended")
            return

        for item in retries:
            step = item.get("step", "")
            reason = item.get("reason", "")
            params = item.get("params", {})
            self._log(f"[Think] Retrying {step}: {reason}", "warn")
            if step == "xss":
                self._safe_step("Adaptive_XSS", self._adaptive_xss, params)
            elif step == "sqli_blind":
                self._safe_step("Adaptive_SQLi_Blind", self._adaptive_sqli_blind, params)
            elif step == "file_fuzz":
                self._safe_step("Adaptive_FileFuzz", self._adaptive_file_fuzz, params)

    # -- Adaptive retry methods --------------------------------------------

    def _adaptive_xss(self, params: dict = None):
        """
        Aggressive XSS retry - targets DOM sinks and additional parameters.
        Driven by Think_And_Adapt when initial XSS step found nothing.
        """
        params = params or {}
        from app.modules.experimental_agent.llm_engine import SECLISTS_EMBEDDED
        payloads = SECLISTS_EMBEDDED.get('xss', [])

        # Collect targets including any found paths from dir enum
        targets = self._collect_xss_targets()
        extra_params = ["q", "search", "input", "value", "data", "content",
                        "text", "body", "message", "comment", "name", "title"]

        confirmed = 0
        for url in targets[:10]:
            for param in extra_params:
                result = self.verifier.verify_xss(url, param)
                if result["confirmed"]:
                    self._log(f"[AdaptiveXSS] CONFIRMED {url} param={param}", "high")
                    ai_payload = self.llm.generate_poc_payload(
                        'xss', param, result['snippet'], result['snippet'], url
                    )
                    self.memory.add_finding(
                        self.host, 'adaptive_xss', 'xss',
                        f"GET {result['url']}\n"
                        f"Context: {result['context']}\n"
                        f"AI_PAYLOAD: {ai_payload}\n\n"
                        f"Snippet:\n{result['snippet']}",
                        f"XSS (adaptive) - {url} param={param}",
                        severity='High',
                    )
                    confirmed += 1
                    break   # one finding per URL
            if confirmed >= 3:
                break
        self._log(f"[AdaptiveXSS] {confirmed} additional finding(s)")

    def _adaptive_sqli_blind(self, params: dict = None):
        """
        Time-based blind SQLi retry using SLEEP payloads.
        Driven by Think_And_Adapt when initial SQLi found nothing.
        """
        params = params or {}
        from app.modules.experimental_agent.llm_engine import SECLISTS_EMBEDDED
        blind_payloads = SECLISTS_EMBEDDED.get('sqli_blind', [])[:6]

        targets = self._collect_xss_targets()
        confirmed = 0

        for url in targets[:5]:
            for payload in blind_payloads:
                result = self.verifier.verify_sqli(url, "id", payload)
                if result["confirmed"]:
                    self._log(f"[AdaptiveSQLi] CONFIRMED blind - {url}", "high")
                    ai_payload = self.llm.generate_poc_payload(
                        'sqli', 'id', payload, result['snippet'], url
                    )
                    self.memory.add_finding(
                        self.host, 'adaptive_sqli', 'sqli',
                        f"GET {result['url']}\n"
                        f"Error: {result['error_match']}\n"
                        f"AI_PAYLOAD: {ai_payload}\n\n"
                        f"Snippet:\n{result['snippet']}",
                        f"Blind SQLi (adaptive) - {url}",
                        severity='Critical',
                    )
                    confirmed += 1
                    break
        self._log(f"[AdaptiveSQLi] {confirmed} blind injection(s) confirmed")

    def _adaptive_file_fuzz(self, params: dict = None):
        """
        Extended file fuzz with additional backup and config extensions.
        Driven by Think_And_Adapt when initial file fuzz found nothing.
        """
        params = params or {}
        extra_paths = [
            "config.bak", "config.old", "config.php.bak", "settings.bak",
            "database.bak", "db.bak", ".env.bak", ".env.old", ".env.local",
            "web.config.bak", "app.config.bak", "secrets.yaml", "secrets.json",
            "credentials.json", "application.properties.bak",
        ] + params.get("extra_paths", [])

        confirmed = 0
        for path in extra_paths:
            result = self.verifier.verify_file(self.base, path)
            if result["status"] == "CONFIRMED":
                self._log(f"[AdaptiveFuzz] CONFIRMED {result['url']}", "high")
                ai_payload = self.llm.generate_poc_payload(
                    'leak', path, '', result['snippet'], result['url']
                )
                self.memory.add_finding(
                    self.host, 'fuzzer_adaptive', 'leak',
                    f"GET {result['url']}\nHTTP 200 OK\n"
                    f"AI_PAYLOAD: {ai_payload}\n\n{result['snippet']}",
                    f"Sensitive file exposed (adaptive): {path}",
                    severity='High',
                )
                confirmed += 1
        self._log(f"[AdaptiveFuzz] {confirmed} additional file(s) confirmed")

    # -- Step 8: LLM threat analysis ---------------------------------------

    def _step_llm_analysis(self):
        findings = self.memory.get_detailed_findings(self.host, since=self._scan_start)
        raw_ev   = "\n".join(self.evidence[-80:])   # last 80 lines of evidence

        if not findings:
            self._log("[LLM] No confirmed findings to analyse - skipping")
            return "No confirmed findings to analyse."

        self._log(f"[LLM] Sending {len(findings)} confirmed findings to WhiteRabbitNeo ...")
        analysis = self.llm.analyze_findings(self.host, findings, raw_ev)
        self._log(f"[LLM] Analysis complete ({len(analysis)} chars)")

        self.memory.add_finding(
            self.host, "llm_analysis", "tech",
            analysis,
            "LLM threat analysis complete",
            severity="Info",
        )
        return analysis

    # -- Main run ----------------------------------------------------------

    def run(self) -> dict:
        from datetime import datetime as _dt
        start = time.time()
        # Record the moment this scan starts - used to scope findings to this
        # session only, filtering out stale entries from previous scans
        self._scan_start = _dt.now().isoformat()
        self.memory.upsert_target(self.host)

        if self._wildcard:
            # -- *.example.com  /  *.example.com/*/* -----------------------
            mode_label = (
                f"Subdomain + Directory ({'/'.join(self._dir_segments)})"
                if self._dir_wildcard else "Subdomain"
            )
            self._log(f"[*] {mode_label} mode - {self._base_domain}", "step")
            self._safe_step("Subdomain_Enum", self._step_subdomain_enum)

            if not self._live_subdomains:
                self._log("[!] No live subdomains found", "warn")
                return self._build_result("No live subdomains discovered.",
                                          elapsed=round(time.time()-start, 1))

            for sub_url in self._live_subdomains:
                if self._dir_wildcard:
                    # Combined mode: scan subdomain AND run dir enum on it
                    self._safe_step(f"Scan:{sub_url}", self._scan_subdomain, sub_url)
                    # Point dir enum base at this subdomain and enumerate
                    orig_dir_base   = self._dir_base if hasattr(self, "_dir_base") else sub_url
                    self._dir_base  = sub_url
                    self._found_dirs = []
                    self._safe_step(f"DirEnum:{sub_url}", self._step_dir_enum)
                    self._dir_base  = orig_dir_base
                else:
                    self._safe_step(f"Scan:{sub_url}", self._scan_subdomain, sub_url)

            self._safe_step("SSRF_Check",       self._step_ssrf)
            self._safe_step("OpenRedirect",     self._step_open_redirect)
            self._safe_step("XXE_Check",        self._step_xxe)
            self._safe_step("Nikto",            self._step_nikto)
            self._safe_step("Think_And_Adapt",  self._think_and_adapt)

        elif self._dir_wildcard:
            # -- example.com/*  /  example.com/*/*  -> directory enum --------
            star_count = self._dir_segments.count("*")
            self._log(
                f"[*] Directory mode - {star_count} level(s) deep, "
                f"template: /{'/'.join(self._dir_segments)}", "step"
            )
            # Reachability check on base host first
            reachable = self._safe_step("Reachability", self._step_reachability)
            if not reachable:
                return self._build_result("Unreachable",
                                          elapsed=round(time.time()-start, 1))

            self._safe_step("Fingerprint",     self._step_fingerprint)
            self._safe_step("Header_Security", self._step_header_security)
            self._safe_step("Dir_Enum",        self._step_dir_enum)
            self._safe_step("File_Fuzz",        self._step_fuzz_files)
            self._safe_step("Secrets",          self._step_secrets)
            self._safe_step("SSRF_Check",       self._step_ssrf)
            self._safe_step("OpenRedirect",     self._step_open_redirect)
            self._safe_step("XXE_Check",        self._step_xxe)
            self._safe_step("Nikto",            self._step_nikto)
            self._safe_step("Think_And_Adapt",  self._think_and_adapt)

        else:
            # -- Normal single-URL scan -------------------------------------
            reachable = self._safe_step("Reachability", self._step_reachability)
            if not reachable:
                return self._build_result("Unreachable",
                                          elapsed=round(time.time()-start, 1))

            self._safe_step("Fingerprint",     self._step_fingerprint)
            self._safe_step("Header_Security", self._step_header_security)
            self._safe_step("File_Fuzz",       self._step_fuzz_files)
            self._safe_step("Secrets",         self._step_secrets)
            self._safe_step("SQLi_Check",       self._step_sqli)
            self._safe_step("XSS_Check",        self._step_xss)
            self._safe_step("SSRF_Check",       self._step_ssrf)
            self._safe_step("OpenRedirect",     self._step_open_redirect)
            self._safe_step("XXE_Check",        self._step_xxe)
            self._safe_step("Nikto",            self._step_nikto)
            self._safe_step("Think_And_Adapt",  self._think_and_adapt)

        analysis = self._safe_step("LLM_Analysis", self._step_llm_analysis) or ""

        elapsed = round(time.time() - start, 1)
        self._log(f"[DONE] Scan completed in {elapsed}s")
        return self._build_result(analysis, elapsed)

    def _build_result(self, analysis: str, elapsed=0) -> dict:
        # Only include findings from THIS scan session (not accumulated old runs)
        _all_findings = self.memory.get_detailed_findings(
            self.host, since=self._scan_start
        )
        # Exclude Low and Info severity findings from the report output
        _excluded = {"Low", "Info"}
        findings = [
            f for f in _all_findings
            if f.get("severity", "Info") not in _excluded
        ]
        sev_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4, "Info": 5}
        risk = min(
            (f.get("severity", "Info") for f in findings),
            key=lambda s: sev_order.get(s, 99),
            default="Info",
        )
        return {
            "target":   self.target,
            "findings": findings,
            "analysis": analysis,
            "evidence": self.evidence,
            "step_log": self.step_log,
            "risk":     risk,
            "elapsed":  elapsed,
        }
