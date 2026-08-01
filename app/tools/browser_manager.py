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
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


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

        Returns:
            dict: `{vulnerability_type, url, payload, note, screenshot_path,
            timestamp}` - JSON-serializable evidence, matching
            `VulnerabilityReportWriter`'s expected input shape.

        Raises:
            BrowserManagerError: If Playwright isn't installed and
                auto-start fails, or if navigation/screenshot itself fails.
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
        filename = (
            f"{vulnerability_type}_{safe_host}_"
            f"{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.png"
        )
        screenshot_path = os.path.join(self.screenshot_dir, filename)

        try:
            self._page.goto(url, timeout=self.nav_timeout_ms)
            self._page.screenshot(path=screenshot_path, full_page=True)
        except Exception as e:
            raise BrowserManagerError(
                f"Screenshot capture failed for {url}: {e}"
            ) from e

        evidence = {
            "vulnerability_type": vulnerability_type,
            "url": url,
            "payload": payload,
            "note": note,
            "screenshot_path": screenshot_path,
            "timestamp": timestamp.isoformat(),
        }
        logger.info(
            "Captured %s evidence for %s -> %s",
            vulnerability_type, url, screenshot_path,
        )
        return evidence

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

    def __enter__(self) -> "BrowserManager":
        self.start(self.target or "")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
