"""Breadth-first HTML crawler that harvests injection points.

The crawler's product is not a list of URLs - it is the set of
`(endpoint, parameter)` pairs that `PathTraversalScanner` can inject its
existing payload matrix into. Every design choice here serves that:

  * Parsing moved from a shell pipeline into Python. The old
    `grep -oE '(href|src)="[^"]+"'` demanded a literal `="` with double
    quotes, so single-quoted markup, `data-src`, and `<form action=...>`
    were structurally invisible - the regexes below match what
    `path_traversal.py::_extract_page_endpoints` already matched.
  * Injection points are collapsed by `(path, parameter-set)`. Twenty
    product thumbnails at `/image?filename=1.jpg` .. `?filename=20.jpg` are
    ONE injection point; `sort -u` deduped by string, so those twenty
    consumed the entire persist budget and pushed genuinely distinct
    endpoints (`/product?productId=`) out of memory entirely.
  * Findings are written on two channels: `data_type="param"` (the explicit
    `endpoint\tparam` handoff consumed by
    `PathTraversalScanner._discover_injection_points_tiered`) and the
    legacy `data_type="link"`, so nothing that already reads links regresses.
"""

import re
from urllib.parse import urljoin, urlparse

from app.tools.utils import normalize_domain_for_memory, shell_quote

# Permissive attribute harvest, deliberately kept in step with
# path_traversal.py::_extract_page_endpoints' own regex: either quote style,
# arbitrary whitespace around `=`. `action` is included because a GET form is
# an injection point that never appears as a `?param=` anywhere in the markup.
_ATTR_RE = re.compile(
    r'''(?:href|src|action|data-src|data-url)\s*=\s*["']([^"']+)["']''',
    re.IGNORECASE,
)
_FORM_RE = re.compile(r"<form\b([^>]*)>(.*?)</form>", re.IGNORECASE | re.DOTALL)
_ACTION_RE = re.compile(r'''action\s*=\s*["']([^"']+)["']''', re.IGNORECASE)
_INPUT_NAME_RE = re.compile(
    r'''<(?:input|textarea|select)\b[^>]*\bname\s*=\s*["']([^"']+)["']''',
    re.IGNORECASE,
)
_FORM_METHOD_RE = re.compile(r'''method\s*=\s*["']?(get|post)''', re.IGNORECASE)

# JavaScript-discovered endpoints. Deliberately regex, not a JS parser: the
# goal is only to surface request targets an attribute scan cannot see (an
# endpoint built inside a fetch/axios call or an XHR open()). Two passes:
#   1. Explicit request calls - fetch("..."), axios.get('...'), .open("GET", ...),
#      and object literals like `url: "/api/x"`.
#   2. Any remaining quoted string that looks like a rooted path, which catches
#      hand-rolled string concatenation the call patterns miss.
# Both are confined to <script> bodies so ordinary prose can never match.
_SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.IGNORECASE | re.DOTALL)
_JS_CALL_RE = re.compile(
    r"""(?:fetch|axios(?:\.(?:get|post|put|delete))?|\.open|\.ajax|url\s*:|href\s*=|src\s*=)"""
    r"""\s*\(?\s*(?:["'](?:GET|POST|PUT|DELETE)["']\s*,\s*)?["']([^"'\s]+)["']""",
    re.IGNORECASE,
)
_JS_PATH_RE = re.compile(r"""["'](/[A-Za-z0-9_\-./]*\?[A-Za-z0-9_\-\[\]=&%.+/]*)["']""")
# Same character class path_traversal.py uses when re-parsing stored links, so
# a name harvested here is never one the scanner would then fail to recover.
_PARAM_RE = re.compile(r"[?&]([A-Za-z0-9_\-\[\]]+)=")

# Parameter names that historically front a filesystem sink. Used ONLY to rank
# the persist queue - never to filter - so an unusual name still reaches memory
# when budget allows. Kept in step with path_traversal.py's `high_signal` set.
_FILE_ISH = frozenset({
    "filename", "file", "path", "page", "doc", "document",
    "include", "download", "template", "view", "name", "item", "lang",
})

_SKIP_SCHEMES = ("javascript:", "mailto:", "tel:", "data:", "blob:")
# Extensions worth harvesting as endpoints but never worth *fetching* as HTML.
_ASSET_EXT = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map", ".pdf", ".zip",
)
_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")

# Separator for the `data_type="param"` raw_data payload. A tab cannot occur in
# a URL or an HTML attribute name, so the two halves are always recoverable.
PARAM_FINDING_SEP = "\t"


class CrawlerService:
    """Discovers internal links and entry points to expand the attack surface."""

    def __init__(self, runner, memory):
        """Store the shared command runner and memory service.

        Args:
            runner: Object with a `run(command, timeout=...)` method that
                executes a shell command (via WSL/SSH) and returns its output
                as a str.
            memory (ArgusMemory): Blackboard memory service used to persist
                discovered links and injection points.

        Raises:
            TypeError: If either collaborator is omitted - both are required
                for every crawl operation, and failing fast here beats an
                AttributeError surfacing mid-crawl.
        """
        if runner is None or memory is None:
            raise TypeError(
                "CrawlerService requires both a command runner and a memory service"
            )
        self.runner = runner
        self.memory = memory

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------
    def _fetch(self, url: str) -> str:
        """Fetch one page's HTML, returning "" on any failure.

        `--max-time`/`--connect-timeout` bound the call inside curl itself
        rather than relying on command_runner.py's much longer generic
        default, so an unreachable target fails fast instead of blocking the
        whole crawl budget.

        Args:
            url (str): Absolute URL to fetch.

        Returns:
            str: Response body, or "" if the request failed or timed out.
        """
        cmd = (
            f"curl -s -L --http1.1 --max-time 15 --connect-timeout 5 "
            f"-H {shell_quote(f'User-Agent: {_UA}')} {shell_quote(url)}"
        )
        try:
            return self.runner.run(cmd, timeout=20) or ""
        except TypeError:
            # Runner implementations without a `timeout` kwarg (and MagicMocks
            # configured with a strict spec) must not abort the crawl.
            try:
                return self.runner.run(cmd) or ""
            except Exception:
                return ""
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def params_of(link: str) -> list[str]:
        """Return the query-parameter names carried by `link`, in order.

        Args:
            link (str): Absolute or relative URL.

        Returns:
            list[str]: Deduplicated parameter names; empty when `link`
            carries no query string.
        """
        seen: set[str] = set()
        out: list[str] = []
        for name in _PARAM_RE.findall(link):
            if name not in seen:
                seen.add(name)
                out.append(name)
        return out

    @classmethod
    def _signature(cls, link: str) -> tuple:
        """Collapse key identifying one injection point.

        An injection point is `(host, path, parameter-name-set)` - parameter
        *values* are irrelevant, because the scanner overwrites them with its
        payloads. Collapsing on this is what stops a page full of
        `/image?filename=<n>.jpg` thumbnails from consuming the persist
        budget twenty times over for a single real sink.

        Args:
            link (str): Absolute URL.

        Returns:
            tuple: `(netloc, path, sorted parameter names)`.
        """
        parsed = urlparse(link)
        return (parsed.netloc, parsed.path, tuple(sorted(cls.params_of(link))))

    @classmethod
    def _rank(cls, link: str) -> int:
        """Persist priority for `link`: lower is written to memory first.

        Args:
            link (str): Absolute URL.

        Returns:
            int: 0 when the link carries a file-ish parameter name (the
            likeliest traversal sink), 1 for any other parameter-bearing
            link, 2 for a link with no parameters at all.
        """
        names = [n.lower() for n in cls.params_of(link)]
        if not names:
            return 2
        return 0 if any(n in _FILE_ISH for n in names) else 1

    def _in_scope(self, raw: str, page_url: str, host: str) -> str:
        """Resolve `raw` against `page_url` and return it only if in scope.

        Args:
            raw (str): A raw href/src/action value or a JS-extracted string.
            page_url (str): URL the value was found on; base for resolution.
            host (str): Hostname the resolved URL must match.

        Returns:
            str: The absolute URL, or "" if it is empty, a non-navigational
            scheme, a bare fragment, or off-host.
        """
        raw = (raw or "").strip()
        if not raw or raw.startswith("#") or raw.lower().startswith(_SKIP_SCHEMES):
            return ""
        absolute = urljoin(page_url, raw)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https") or parsed.hostname != host:
            return ""
        return absolute

    def _harvest(self, html: str, page_url: str, host: str) -> list[tuple[str, str]]:
        """Extract same-host absolute URLs from one page, with provenance.

        Covers all four surfaces the integrated pipeline needs:

          * `href`/`src`/`action`/`data-src`/`data-url` attributes -> "html"
          * `<form>` action + field names, emitted as a synthesized
            `action?name=` URL -> "form". Keeping one URL-shaped
            representation for every injection point means the collapse,
            ranking and persistence paths need no special case, and the
            scanner's own link re-parser recovers the field name unchanged.
          * endpoints referenced inside `<script>` bodies -> "js"
          * query parameters, which are carried on the URLs above and parsed
            out by `params_of()`.

        Args:
            html (str): Raw response body.
            page_url (str): URL the body came from; the base for resolving
                relative references.
            host (str): Hostname a discovered URL must match to stay in scope.
                External links (CDNs, social buttons) are dropped here rather
                than downstream, so they never consume the persist budget.

        Returns:
            list[tuple[str, str]]: `(absolute_url, source)` in discovery
            order, where source is "html", "form", or "js".
        """
        out: list[tuple[str, str]] = []

        for match in _ATTR_RE.finditer(html):
            absolute = self._in_scope(match.group(1), page_url, host)
            if absolute:
                out.append((absolute, "html"))

        for attrs, body in _FORM_RE.findall(html):
            action_match = _ACTION_RE.search(attrs)
            action = (
                urljoin(page_url, action_match.group(1).strip())
                if action_match else page_url
            )
            parsed_action = urlparse(action)
            if parsed_action.hostname != host:
                continue
            separator = "&" if parsed_action.query else "?"
            for name in _INPUT_NAME_RE.findall(body):
                name = name.strip()
                if name:
                    out.append((f"{action}{separator}{name}=", "form"))

        for script in _SCRIPT_RE.findall(html):
            for candidate in _JS_CALL_RE.findall(script) + _JS_PATH_RE.findall(script):
                absolute = self._in_scope(candidate, page_url, host)
                if absolute:
                    out.append((absolute, "js"))

        return out

    def _form_methods(self, html: str, page_url: str, host: str) -> dict[str, str]:
        """Map each form action URL to its HTTP method.

        The scanner injects via the query string, so a POST-only form is
        recorded but flagged - it is reported as a lower-confidence surface
        rather than silently probed as if it were a GET.

        Args:
            html (str): Raw response body.
            page_url (str): URL the body came from.
            host (str): In-scope hostname.

        Returns:
            dict[str, str]: Action URL -> "GET" or "POST".
        """
        methods: dict[str, str] = {}
        for attrs, _body in _FORM_RE.findall(html):
            action_match = _ACTION_RE.search(attrs)
            action = (
                urljoin(page_url, action_match.group(1).strip())
                if action_match else page_url
            )
            if urlparse(action).hostname != host:
                continue
            method_match = _FORM_METHOD_RE.search(attrs)
            methods[action] = (
                method_match.group(1).upper() if method_match else "GET"
            )
        return methods

    # ------------------------------------------------------------------
    # Crawl -> normalized attack surface
    # ------------------------------------------------------------------
    def harvest_attack_surface(self, url, max_pages=12, max_depth=2,
                               store_limit=40) -> dict:
        """Crawl `url` and return the normalized attack surface.

        This is the single source of truth for discovery. `crawl_target()`
        wraps it for the agent (string report), and
        `PathTraversalScanner.run_traversal_scan()` consumes the returned dict
        directly - so neither module re-implements HTML parsing.

        Pipeline: crawl (BFS) -> extract (attributes, forms, JS, query
        strings) -> normalize (collapse duplicate sinks, rank, resolve to
        absolute endpoints) -> persist.

        Args:
            url (str): Seed URL. A missing scheme is treated as `http://`.
            max_pages (int): Hard ceiling on pages fetched; each is one curl
                call, so this bounds crawl wall-time.
            max_depth (int): Link-following depth. 0 crawls the seed only.
            store_limit (int): Max endpoints persisted/reported, spent
                highest-rank first so a file-ish parameter is never crowded
                out by parameter-free navigation links.

        Returns:
            dict: `{"target", "host", "pages_fetched", "raw_links",
            "endpoints", "injection_points", "path_segments"}` where
            `endpoints` is a list of
            `{"url", "endpoint", "params", "method", "source"}` dicts,
            `injection_points` is a list of `(endpoint, param)` tuples, and
            `path_segments` lists parameterless same-host endpoints (candidate
            path-segment injection targets).
        """
        print(f"[*] [Argus-Core] Crawling target: {url}")
        seed = url if url.startswith(("http://", "https://")) else f"http://{url}"
        host = urlparse(seed).hostname
        empty = {
            "target": url, "host": host, "pages_fetched": 0, "raw_links": 0,
            "endpoints": [], "injection_points": [], "path_segments": [],
        }
        if not host:
            return empty

        queue: list[tuple[str, int]] = [(seed, 0)]
        visited: set[str] = set()
        discovered: list[tuple[str, str]] = []
        seen_links: set[str] = set()
        methods: dict[str, str] = {}

        while queue and len(visited) < max_pages:
            page, depth = queue.pop(0)
            if page in visited:
                continue
            visited.add(page)

            html = self._fetch(page)
            if not html:
                continue
            methods.update(self._form_methods(html, page, host))

            for link, source in self._harvest(html, page, host):
                if link not in seen_links:
                    seen_links.add(link)
                    discovered.append((link, source))
                # Only recurse into parameter-free, non-asset pages. Following
                # every `?filename=<n>.jpg` variant would spend the entire
                # max_pages budget re-fetching one already-known sink.
                parsed = urlparse(link)
                if (depth < max_depth
                        and not parsed.query
                        and not parsed.path.lower().endswith(_ASSET_EXT)
                        and link not in visited):
                    queue.append((link, depth + 1))

        # Collapse duplicates to one representative per injection point, then
        # order so the likeliest traversal sinks are persisted first.
        collapsed: dict[tuple, tuple[str, str]] = {}
        for link, source in discovered:
            collapsed.setdefault(self._signature(link), (link, source))
        ranked = sorted(collapsed.values(), key=lambda pair: self._rank(pair[0]))

        clean_target = normalize_domain_for_memory(url)
        endpoints: list[dict] = []
        injection_points: list[tuple[str, str]] = []
        path_segments: list[str] = []

        for link, source in ranked[:store_limit]:
            self.memory.add_finding(
                clean_target, "crawler", "link", link, f"Discovered link: {link}"
            )
            parsed = urlparse(link)
            endpoint = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            params = self.params_of(link)
            endpoints.append({
                "url": link,
                "endpoint": endpoint,
                "params": params,
                "method": methods.get(link.split("?")[0], "GET") if source == "form" else "GET",
                "source": source,
            })
            for name in params:
                injection_points.append((endpoint, name))
                self.memory.add_finding(
                    clean_target, "crawler", "param",
                    f"{endpoint}{PARAM_FINDING_SEP}{name}",
                    f"Injection point: {endpoint}?{name}=",
                )
            if not params and parsed.path not in ("", "/"):
                if endpoint not in path_segments:
                    path_segments.append(endpoint)

        return {
            "target": url,
            "host": host,
            "pages_fetched": len(visited),
            "raw_links": len(discovered),
            "endpoints": endpoints,
            "injection_points": injection_points,
            "path_segments": path_segments,
        }

    def crawl_target(self, url, max_pages=12, max_depth=2, store_limit=40):
        """Crawl `url` and return a human/agent-readable attack-surface report.

        Thin formatting wrapper over `harvest_attack_surface()`; the return
        type stays `str` because `WSLBridgeTools.crawl_target` exposes this as
        the LangChain `Crawl_Target` tool, which requires a string.

        Each discovered `(endpoint, parameter)` pair is persisted as a
        `data_type="param"` finding, which
        `PathTraversalScanner._discover_injection_points_tiered` consumes as a
        tier-0 (observed, full-payload-budget) injection point. Links are also
        persisted under the legacy `data_type="link"` channel so existing
        consumers are unaffected.

        Args:
            url (str): Seed URL. A missing scheme is treated as `http://`.
            max_pages (int): Hard ceiling on pages fetched.
            max_depth (int): Link-following depth.
            store_limit (int): Max endpoints persisted/reported.

        Returns:
            str: A crawler report listing the distinct injection points found.
        """
        surface = self.harvest_attack_surface(url, max_pages, max_depth, store_limit)
        return self.format_surface_report(surface)

    @staticmethod
    def format_surface_report(surface: dict) -> str:
        """Render `harvest_attack_surface()` output as the crawler report.

        The wording deliberately names the traversal class when a file-ish
        parameter is present: `react_workflow._extract_vulnerability_hints`
        scans this text to decide whether to hand the model an explicit
        Path_Traversal_Scan directive.

        Args:
            surface (dict): Output of `harvest_attack_surface()`.

        Returns:
            str: The formatted report.
        """
        endpoints = surface["endpoints"]
        injection_points = surface["injection_points"]
        parameterized = [e for e in endpoints if e["params"]]
        by_source: dict[str, int] = {}
        for entry in endpoints:
            by_source[entry["source"]] = by_source.get(entry["source"], 0) + 1
        source_note = ", ".join(f"{k}: {v}" for k, v in sorted(by_source.items()))

        report = (
            f"--- [WEB] CRAWLER REPORT: {surface['target']} ---\n"
            f"Pages fetched: {surface['pages_fetched']} | "
            f"raw links: {surface['raw_links']} | "
            f"injection points: {len(endpoints)} "
            f"(parameterized: {len(parameterized)}, "
            f"params handed off: {len(injection_points)})"
        )
        if source_note:
            report += f"\nSources -> {source_note}"
        if injection_points:
            report += "\nTop injection points:\n" + "\n".join(
                f"{ep}?{name}=" for ep, name in injection_points[:15]
            )
        elif endpoints:
            report += "\nNo parameterized endpoints. Links:\n" + "\n".join(
                e["url"] for e in endpoints[:15]
            )
        if surface["path_segments"]:
            report += (
                "\nParameterless endpoints (path-segment injection candidates): "
                + ", ".join(surface["path_segments"][:8])
            )
        return report


# ----------------------------------------------------------------------
# Standalone pipeline entry point
#
# Inside the agent, CrawlerService is constructed with the real CommandRunner
# (WSL/SSH) and ArgusMemory (SQLite blackboard). Neither is appropriate for a
# one-shot `python -m app.tools.crawler <url>` run: CommandRunner needs a
# configured Kali distro and paramiko, and ArgusMemory would mutate the shared
# blackboard. The two shims below satisfy the exact same duck-typed contracts
# (`run(cmd, timeout=...)` / `add_finding(...)` + `get_detailed_findings(...)`)
# using nothing outside the standard library, so the identical pipeline code
# runs in both contexts. No new module, no new dependency.
# ----------------------------------------------------------------------
class LocalCurlRunner:
    """Minimal `CommandRunner` stand-in that executes curl on this host."""

    def run(self, command: str, timeout: int = 30, **_kwargs) -> str:
        """Execute `command` in the local shell and return its stdout.

        Args:
            command (str): The curl command string built by CrawlerService or
                PathTraversalScanner.
            timeout (int): Seconds before the subprocess is killed.
            **_kwargs: Accepted and ignored, for signature compatibility with
                `CommandRunner.run` (e.g. `show_prompt`).

        Returns:
            str: Captured stdout, or "" on non-zero exit, timeout, or any
            other failure - never raises, matching CommandRunner's contract.
        """
        import subprocess
        try:
            completed = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, encoding="utf-8", errors="ignore",
            )
            return completed.stdout or ""
        except Exception:
            return ""


class InMemoryBlackboard:
    """Minimal `ArgusMemory` stand-in backed by a plain list."""

    def __init__(self):
        """Initialise the finding store."""
        self.findings: list[dict] = []

    def add_finding(self, domain, tool_name, data_type, raw_data, summary,
                    severity="Info") -> None:
        """Record one finding.

        Args:
            domain (str): Normalized target key.
            tool_name (str): Producing tool.
            data_type (str): "link", "param", or "vulnerability".
            raw_data (str): The finding payload.
            summary (str): Human-readable description.
            severity (str): Severity label.

        Returns:
            None
        """
        self.findings.append({
            "domain": domain, "tool_name": tool_name, "data_type": data_type,
            "raw_data": raw_data, "summary": summary, "severity": severity,
        })

    def get_detailed_findings(self, domain, since=None) -> list[dict]:
        """Return every finding recorded for `domain`.

        Args:
            domain (str): Normalized target key.
            since (str | None): Accepted for signature compatibility; ignored.

        Returns:
            list[dict]: Matching findings, oldest first.
        """
        return [f for f in self.findings if f["domain"] == domain]


def run_pipeline(url, max_pages=12, max_depth=2, runner=None, memory=None,
                 **scan_kwargs) -> dict:
    """Run the full integrated pipeline against `url`.

    crawl -> extract -> normalize -> pass -> test payloads -> report.

    Args:
        url (str): Target base URL.
        max_pages (int): Crawl page ceiling.
        max_depth (int): Crawl link-following depth.
        runner: Command runner; defaults to `LocalCurlRunner()`.
        memory: Blackboard; defaults to `InMemoryBlackboard()`.
        **scan_kwargs: Forwarded to `PathTraversalScanner.run_traversal_scan`.

    Returns:
        dict: `{"surface", "crawler_report", "scan_report", "findings"}`,
        where `findings` are the confirmed-traversal memory records.
    """
    # Imported here, not at module scope: path_traversal imports FROM this
    # module (PARAM_FINDING_SEP, CrawlerService), so a top-level import back
    # would be circular.
    from app.tools.path_traversal import PathTraversalScanner

    runner = runner or LocalCurlRunner()
    memory = memory or InMemoryBlackboard()

    crawler = CrawlerService(runner, memory)
    surface = crawler.harvest_attack_surface(url, max_pages=max_pages,
                                             max_depth=max_depth)
    crawler_report = crawler.format_surface_report(surface)

    scanner = PathTraversalScanner(runner, memory)
    scan_report = scanner.scan_attack_surface(surface, **scan_kwargs)

    domain = normalize_domain_for_memory(url)
    findings = [
        f for f in memory.get_detailed_findings(domain)
        if f["data_type"] == "vulnerability"
    ]
    return {
        "surface": surface,
        "crawler_report": crawler_report,
        "scan_report": scan_report,
        "findings": findings,
    }


def main(argv=None) -> int:
    """CLI entry point: crawl a target and scan its attack surface.

    Args:
        argv (list[str] | None): Argument vector; defaults to `sys.argv[1:]`.

    Returns:
        int: 0 when the scan completed, 2 when a traversal was confirmed
        (so shell callers can branch on a finding), 1 on bad input.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Crawl a target, harvest its attack surface, and probe "
                    "every discovered parameter for path traversal / LFI.",
    )
    parser.add_argument("url", help="Target base URL, e.g. https://target/")
    parser.add_argument("--max-pages", type=int, default=12,
                        help="Max pages to fetch during the crawl (default 12)")
    parser.add_argument("--max-depth", type=int, default=2,
                        help="Link-following depth (default 2)")
    parser.add_argument("--max-total-probes", type=int, default=720,
                        help="Global probe ceiling (default 720)")
    args = parser.parse_args(argv)

    if not args.url.startswith(("http://", "https://")):
        args.url = f"http://{args.url}"

    outcome = run_pipeline(
        args.url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        max_total_probes=args.max_total_probes,
    )

    print(outcome["crawler_report"])
    print()
    print(outcome["scan_report"])

    if outcome["findings"]:
        print(f"\n[+] {len(outcome['findings'])} confirmed traversal finding(s).")
        return 2
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
