"""Persistent Playwright-backed headless browser session for capturing
visual proof-of-concept evidence of confirmed vulnerabilities
(specs/029-vulnerability-screenshot-evidence).

Deliberately NOT the same shape as `specs/022-browser-automation-playwright`'s
(proposed, unimplemented) design: that spec launches a fresh, stateless
subprocess inside Kali per call for DOM-rendering purposes. This module runs
directly in the Windows-host Python process (matching every other pure-Python
`app/tools/` service, e.g. `EvasionService`), and is intentionally a single
persistent session - opened once (`start()`), reused across every capture
call for the whole test run, closed once (`close()`) - because its job is to
photograph a URL Argus already knows is vulnerable, not to render arbitrary
JS-heavy pages via Kali's toolchain.
"""
import logging
import os
import re
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# MIME types Chromium renders as readable text or markup on its own. Anything
# outside this set is treated as "the browser may not be able to show this",
# which matters because a path-traversal endpoint such as PortSwigger's
# `/image?filename=...` answers with `Content-Type: image/jpeg` even when the
# traversal makes it return /etc/passwd. Chromium then paints a broken-image
# placeholder and the screenshot proves nothing - see `_inspect_response`.
_TEXTUAL_MIME_PREFIXES = ("text/",)
_TEXTUAL_MIME_EXACT = frozenset({
    "application/json",
    "application/ld+json",
    "application/xml",
    "application/xhtml+xml",
    "application/javascript",
    "application/x-javascript",
})

# Cap on how much response text is copied into the evidence dict / JSON
# report. The screenshots are the browser's own; this is just the excerpt
# that travels with them.
_EVIDENCE_BODY_LIMIT = 8000


class BrowserManagerError(RuntimeError):
    """Raised for an honest, actionable failure - e.g. Playwright not
    installed - instead of letting a raw ImportError/traceback bubble up
    uncaught (specs/029 NFR-003, matching this project's existing
    honest-error convention, e.g. wsl_bridge.py/evasion.py's stealth_run)."""


class BrowserManager:
    """Owns one Playwright browser/context for the lifetime of a test run.

    Usage::

        bm = BrowserManager()
        bm.start("https://example.com")
        evidence = bm.capture_vulnerability("path_traversal", "https://example.com/?item=../../../../etc/passwd")
        ...  # more captures against the same session
        bm.close()

    or as a context manager::

        with BrowserManager() as bm:
            bm.capture_vulnerability(...)
    """

    def __init__(
        self,
        screenshot_dir: str = "artifacts/screenshots",
        headless: bool = True,
        nav_timeout_ms: int = 30000,
    ):
        """Store configuration only - no Playwright object is created until
        `start()` (or the first `capture_vulnerability()` call, which
        auto-starts) actually needs one, so importing/constructing this
        class never fails on a machine without Playwright installed; only
        *using* it does, with `BrowserManagerError`'s specific message.

        Args:
            screenshot_dir (str): Directory screenshots are saved under,
                created on first use if missing.
            headless (bool): Whether Chromium runs headless. Kept as an
                init-time option (not hardcoded) so a test/debug caller can
                open a visible browser.
            nav_timeout_ms (int): Per-navigation timeout in milliseconds
                (specs/029 NFR-002) - a hung target page must not block the
                whole probe run indefinitely.
        """
        self.screenshot_dir = screenshot_dir
        self.headless = headless
        self.nav_timeout_ms = nav_timeout_ms

        self.target: Optional[str] = None
        # Typed `Any` (not a concrete Playwright class) since the
        # `playwright` package itself is an optional, deferred import
        # (NFR-003) - annotating with its real types would force an
        # unconditional top-level import this module deliberately avoids.
        self._playwright: Optional[Any] = None
        self._browser: Optional[Any] = None
        self._context: Optional[Any] = None
        self._page: Optional[Any] = None
        # host -> path of that site's landing-page screenshot. Photographing
        # the site itself is per-target context, not per-finding evidence, so
        # it is taken once and reused across every finding on that host.
        self._site_shots: Dict[str, str] = {}

    @property
    def is_started(self) -> bool:
        """Whether an active Chromium session is currently held open."""
        return self._browser is not None

    def start(self, target: str = "") -> "BrowserManager":
        """Launch Chromium once and record `target`.

        Idempotent: if a session is already open, this is a no-op (the
        existing session keeps running - callers don't need to track
        whether they already called `start()`, matching the "opens once,
        stays open until the test ends" lifecycle specs/029 asks for).

        Args:
            target (str): The test's target URL/host, recorded for
                reference only (not itself navigated to - each
                `capture_vulnerability()` call supplies its own URL).

        Returns:
            BrowserManager: self, for `bm = BrowserManager().start(url)` chaining.

        Raises:
            BrowserManagerError: If the `playwright` package is not
                installed, or the browser fails to launch.
        """
        self.target = target or self.target
        if self.is_started:
            return self

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise BrowserManagerError(
                "Playwright is not installed - run "
                "`pip install playwright && playwright install chromium`."
            ) from e

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._context = self._browser.new_context()
            self._page = self._context.new_page()
            self._page.set_default_navigation_timeout(self.nav_timeout_ms)
        except Exception as e:
            # Don't leave a half-initialized session behind on a failed launch.
            self.close()
            raise BrowserManagerError(f"Failed to launch headless browser: {e}") from e

        return self

    def capture_vulnerability(
        self,
        vulnerability_type: str,
        url: str,
        payload: Optional[str] = None,
        note: Optional[str] = None,
    ) -> dict:
        """Navigate to `url` and save a full-page screenshot as evidence.

        Auto-starts the session (with `target=url`) if `start()` hasn't
        been called yet, so a caller that only ever wants a single one-off
        capture doesn't have to call `start()` first.

        Args:
            vulnerability_type (str): Short label, e.g. `"path_traversal"` -
                used verbatim in the evidence dict and the screenshot
                filename.
            url (str): The exact URL (including the confirmed payload as a
                query string, if applicable) to navigate to and photograph.
            payload (str, optional): The specific payload string that
                triggered this finding, recorded for traceability.
            note (str, optional): Human-readable summary of the finding
                (e.g. `SENSITIVE_CONTENT_INDICATORS`'s matched description).

        The browser walks the finding's steps and photographs each one.
        Every PNG is Chromium rendering something the target server actually
        sent - nothing here is drawn or composed by Argus:

        1. `site_{host}_*.png` - the target website's own landing page. Taken
           once per host (see `capture_site_context`) and shared by every
           finding on that host: it answers "what site was tested?".
        2. `*_exploit.png` - the browser at the payload URL, rendered exactly
           as the server's response told it to.
        3. `*_response.png` - the same URL under Chromium's built-in
           `view-source:`, which displays the raw response body as text.

        Step 3 exists because step 2 alone is often unreadable. A traversal
        endpoint such as PortSwigger's `/image?filename=...` keeps answering
        with `Content-Type: image/jpeg` even when the traversal makes it
        return /etc/passwd, so Chromium paints only a broken-image
        placeholder. `view-source:` is the browser's own way of showing what
        really came back, with no header rewriting and no synthetic markup.

        2026-08-23: when that mislabeling happens AND step 3 succeeds, step
        2's placeholder file (a near-solid-black frame with a small broken-
        icon graphic - proof a request happened, but no readable evidence)
        is deleted from disk rather than left sitting in
        `artifacts/screenshots/` as confusing clutter next to the real
        proof. `exploit_screenshot_path`/the corresponding `steps` entry is
        then `None`/absent. If step 3 itself fails, the placeholder is kept
        instead - a broken-icon screenshot proving a request was made is
        still better than no evidence at all for that step.

        Returns:
            dict: `{vulnerability_type, url, payload, note, screenshot_path,
            site_screenshot_path, exploit_screenshot_path,
            response_screenshot_path, screenshots, steps, timestamp,
            capture_mode, http_status, content_type, response_excerpt}` -
            JSON-serializable evidence, matching
            `VulnerabilityReportWriter`'s expected input shape.

            `steps` is the ordered walk-through: one entry per screenshot,
            each with `step`, `action`, `url` and `screenshot`.

            `capture_mode` says which shot is the stronger proof: `"page"`
            when the browser rendered the response readably at step 2, or
            `"view_source"` when only step 3 is legible. `screenshot_path`
            points at that shot, for callers written against the original
            single-screenshot API.

        Raises:
            BrowserManagerError: If Playwright isn't installed and
                auto-start fails, or if step 2 itself fails. Steps 1 and 3
                are best-effort: they are logged and skipped rather than
                costing you a confirmed finding.
        """
        if not self.is_started:
            self.start(target=url)
        # start() either raises BrowserManagerError or leaves _page set -
        # this assertion documents that invariant for mypy, it's not a new
        # runtime check.
        assert self._page is not None

        os.makedirs(self.screenshot_dir, exist_ok=True)

        timestamp = datetime.now()
        safe_host = re.sub(r"[^\w\.-]", "_", url.split("://")[-1].split("/")[0]) or "target"
        stem = (
            f"{vulnerability_type}_{safe_host}_"
            f"{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
        )
        exploit_screenshot_path = os.path.join(self.screenshot_dir, f"{stem}_exploit.png")
        response_screenshot_path = os.path.join(self.screenshot_dir, f"{stem}_response.png")

        steps: List[Dict[str, Any]] = []

        # --- step 1: the website itself -----------------------------------
        # The payload URL is often a sub-resource (`/image?filename=...`), so
        # its screenshot shows no site at all. Photograph the target's own
        # landing page too, once per host, so the report shows what was
        # actually tested. Best-effort: a site that will not load must not
        # cost you the finding.
        site_screenshot_path = self.capture_site_context(url)
        if site_screenshot_path:
            steps.append({
                "step": len(steps) + 1,
                "action": "Target site landing page, loaded in the browser",
                "url": self._origin_of(url),
                "screenshot": site_screenshot_path,
            })

        # --- step 2: the payload URL as the browser renders it -------------
        try:
            response = self._page.goto(url, timeout=self.nav_timeout_ms)
            self._page.screenshot(path=exploit_screenshot_path, full_page=True)
        except Exception as e:
            raise BrowserManagerError(
                f"Screenshot capture failed for {url}: {e}"
            ) from e

        http_status, content_type, body_text, renderable = self._inspect_response(response)

        # --- step 3: Chromium's own view of the raw response ---------------
        # `view-source:` is a browser feature, not something Argus builds:
        # Chromium re-requests the URL and prints the bytes it got back. No
        # header is rewritten and no markup is authored, so the screenshot
        # is still the browser showing the server's real answer.
        # Best-effort: step 2 is already on disk either way.
        view_source_url = f"view-source:{url}"
        view_source_ok = False
        try:
            self._page.goto(view_source_url, timeout=self.nav_timeout_ms)
            self._page.screenshot(path=response_screenshot_path, full_page=True)
            view_source_ok = True
        except Exception as e:
            logger.warning("view-source capture failed for %s: %s", url, e)
            response_screenshot_path = ""

        # 2026-08-23 live-run finding: a server that mislabels this
        # response's Content-Type (PortSwigger's own `/image?filename=...`
        # always answers `image/jpeg`, even when the traversal makes it
        # return plain text like /etc/passwd) guarantees step 2's shot is
        # nothing but Chromium's broken-image placeholder - proof a
        # request happened, but no readable evidence, and confusing
        # clutter once step 3 already has the real proof. Delete it rather
        # than leaving it on disk. If step 3 itself also failed, keep the
        # placeholder anyway - a broken-icon screenshot proving a request
        # was made is still better than no evidence at all for this step.
        if not renderable and view_source_ok:
            try:
                if os.path.exists(exploit_screenshot_path):
                    os.remove(exploit_screenshot_path)
            except OSError as e:
                logger.debug(
                    "Could not remove placeholder screenshot %s: %s",
                    exploit_screenshot_path, e,
                )
            exploit_screenshot_path = ""

        if exploit_screenshot_path:
            steps.append({
                "step": len(steps) + 1,
                "action": "Requested the payload URL and rendered the response",
                "url": url,
                "screenshot": exploit_screenshot_path,
            })
        if response_screenshot_path:
            steps.append({
                "step": len(steps) + 1,
                "action": "Raw server response, shown by Chromium's view-source",
                "url": view_source_url,
                "screenshot": response_screenshot_path,
            })

        capture_mode = "page" if renderable else "view_source"
        primary = (
            response_screenshot_path
            if capture_mode == "view_source" and response_screenshot_path
            else exploit_screenshot_path
        )

        evidence = {
            "vulnerability_type": vulnerability_type,
            "url": url,
            "payload": payload,
            "note": note,
            # Legacy single-screenshot key: the most legible of the shots.
            "screenshot_path": primary,
            "site_screenshot_path": site_screenshot_path,
            "exploit_screenshot_path": exploit_screenshot_path or None,
            "response_screenshot_path": response_screenshot_path or None,
            "screenshots": [step["screenshot"] for step in steps],
            "steps": steps,
            "timestamp": timestamp.isoformat(),
            "capture_mode": capture_mode,
            "http_status": http_status,
            "content_type": content_type,
            # The raw proof in text form, so the JSON report stands on its
            # own even if the .png files are lost or unopenable.
            "response_excerpt": (
                body_text[:_EVIDENCE_BODY_LIMIT] if body_text is not None else None
            ),
        }
        logger.info(
            "Captured %s evidence for %s in %d browser steps (primary=%s)",
            vulnerability_type, url, len(steps), capture_mode,
        )
        return evidence

    @staticmethod
    def _origin_of(url: str) -> Optional[str]:
        """`scheme://host/` for `url`, or None if it has no usable origin."""
        parsed = urllib.parse.urlsplit(url)
        if not parsed.scheme or not parsed.netloc:
            return None
        return f"{parsed.scheme}://{parsed.netloc}/"

    def capture_site_context(self, url: str) -> Optional[str]:
        """Photograph the target website's own landing page.

        A finding's URL is frequently a sub-resource rather than a page -
        `/image?filename=...` on PortSwigger's path-traversal labs is the
        standard example - and a screenshot of that URL shows no website at
        all. This captures `scheme://host/` instead, which is the shot a
        report reader means by "a screenshot of the site".

        Taken once per host and cached for the life of the browser session,
        because the site's landing page is the same for every finding on
        that host.

        Args:
            url (str): Any URL on the target; only its scheme and host are
                used.

        Returns:
            str or None: Path of the saved PNG, or None if the site could
            not be photographed. Never raises - site context is nice to
            have, and must never cost you a confirmed finding.
        """
        try:
            parsed = urllib.parse.urlsplit(url)
            if not parsed.scheme or not parsed.netloc:
                return None
            host = parsed.netloc
            cached = self._site_shots.get(host)
            if cached and os.path.isfile(cached):
                return cached

            if not self.is_started:
                self.start(target=url)
            assert self._page is not None

            os.makedirs(self.screenshot_dir, exist_ok=True)
            safe_host = re.sub(r"[^\w\.-]", "_", host) or "target"
            path = os.path.join(
                self.screenshot_dir,
                f"site_{safe_host}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png",
            )

            origin = f"{parsed.scheme}://{host}/"
            self._page.goto(origin, timeout=self.nav_timeout_ms)
            self._page.screenshot(path=path, full_page=True)

            self._site_shots[host] = path
            logger.info("Captured site context for %s -> %s", origin, path)
            return path
        except Exception as e:
            logger.warning("Site context capture failed for %s: %s", url, e)
            return None

    @staticmethod
    def _is_textual_mime(content_type: str) -> bool:
        """Whether Chromium renders this Content-Type as readable text."""
        base = content_type.split(";")[0].strip().lower()
        return base.startswith(_TEXTUAL_MIME_PREFIXES) or base in _TEXTUAL_MIME_EXACT

    @staticmethod
    def _looks_like_text(raw: bytes) -> bool:
        """Whether these bytes are really text, whatever the response claimed.

        A traversal hit returns a text file; a genuine image returns image
        bytes. Only the first case needs the evidence card - a real image
        served as an image renders fine and its own screenshot is the better
        evidence.
        """
        sample = raw[:4096]
        if not sample or b"\x00" in sample:
            return False
        try:
            decoded = sample.decode("utf-8")
        except UnicodeDecodeError:
            return False
        printable = sum(1 for ch in decoded if ch in "\t\r\n" or ch >= " ")
        return printable / len(decoded) >= 0.9

    def _inspect_response(
        self, response: Any
    ) -> Tuple[Optional[int], str, Optional[str], bool]:
        """Classify the navigation response.

        Returns:
            tuple: `(http_status, content_type, body_text, renderable)`.

            `body_text` is the decoded response body when the body is really
            text (whatever Content-Type it claimed), else None.

            `renderable` is True when the browser displayed that response
            readably on its own - a textual Content-Type, or a genuine
            binary image, which shows as an actual picture. It is False when
            the body is text served under a non-textual Content-Type, the
            case where the page screenshot is only a broken-image
            placeholder and the evidence card carries the real proof.

        Never raises: on any inspection problem this reports the response as
        renderable, which is the conservative answer (the page shot is then
        treated as the primary evidence, as it was before this method
        existed).
        """
        try:
            if response is None:
                return None, "", None, True
            status = response.status
            if not isinstance(status, int):
                return None, "", None, True
            headers = response.headers or {}
            content_type = str(headers.get("content-type", ""))

            raw = response.body()
            if not isinstance(raw, (bytes, bytearray)):
                return status, content_type, None, True
            raw = bytes(raw)

            if not self._looks_like_text(raw):
                # Genuine binary - a real image renders as a real image.
                return status, content_type, None, True

            body_text = raw.decode("utf-8", errors="replace")
            return status, content_type, body_text, self._is_textual_mime(content_type)
        except Exception as e:
            logger.debug(
                "Response inspection failed (%s) - treating the page shot as primary.", e
            )
            return None, "", None, True

    def close(self) -> None:
        """Tear the session down in reverse order, swallowing per-step
        errors - a partially-closed session must never raise past this
        call (idempotent: safe to call more than once, or without a prior
        `start()`, matching every other cleanup path in this project's
        tool services)."""
        for handle_name, closer in (
            ("_page", lambda: self._page and self._page.close()),
            ("_context", lambda: self._context and self._context.close()),
            ("_browser", lambda: self._browser and self._browser.close()),
            ("_playwright", lambda: self._playwright and self._playwright.stop()),
        ):
            try:
                closer()
            except Exception as e:
                logger.warning("BrowserManager.close(): %s cleanup failed: %s", handle_name, e)
            finally:
                setattr(self, handle_name, None)
        # The site-context cache is tied to this browser session's lifetime.
        self._site_shots.clear()

    def __enter__(self) -> "BrowserManager":
        self.start(self.target or "")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
