import sys
from unittest.mock import MagicMock, patch

import pytest

from app.tools.browser_manager import BrowserManager, BrowserManagerError

pytestmark = pytest.mark.unit


def _fake_playwright_module():
    """Build a fake `playwright.sync_api` module matching the call chain
    `BrowserManager.start()` expects:
    `sync_playwright().start().chromium.launch().new_context().new_page()`.

    Returns the fake module plus each mocked handle, so tests can assert on
    call counts at any level of the chain (e.g. `chromium.launch` to prove
    SC-001's "launched exactly once" claim).
    """
    fake_page = MagicMock(name="page")
    fake_context = MagicMock(name="context")
    fake_context.new_page.return_value = fake_page
    fake_browser = MagicMock(name="browser")
    fake_browser.new_context.return_value = fake_context
    fake_pw_instance = MagicMock(name="playwright_instance")
    fake_pw_instance.chromium.launch.return_value = fake_browser
    fake_sync_playwright_cm = MagicMock(name="sync_playwright_return")
    fake_sync_playwright_cm.start.return_value = fake_pw_instance

    fake_module = MagicMock(name="playwright.sync_api")
    fake_module.sync_playwright = MagicMock(name="sync_playwright", return_value=fake_sync_playwright_cm)
    return fake_module, fake_pw_instance, fake_browser, fake_context, fake_page


@pytest.fixture
def fake_playwright():
    fake_module, pw_instance, browser, context, page = _fake_playwright_module()
    with patch.dict(sys.modules, {"playwright.sync_api": fake_module}):
        yield fake_module, pw_instance, browser, context, page


class TestBrowserManagerLifecycle:
    def test_start_launches_chromium_exactly_once(self, fake_playwright, tmp_path):
        """SC-001: start() + two capture_vulnerability() calls launch
        Chromium exactly once - proving the persistent-session design, not
        a fresh-launch-per-call model."""
        _module, pw_instance, _browser, _context, page = fake_playwright
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        bm.start("http://example.com")
        bm.capture_vulnerability("path_traversal", "http://example.com/?item=../../etc/passwd")
        bm.capture_vulnerability("path_traversal", "http://example.com/?item=web.config")

        assert pw_instance.chromium.launch.call_count == 1
        assert page.goto.call_count == 2
        assert page.screenshot.call_count == 2
        bm.close()

    def test_start_is_idempotent(self, fake_playwright, tmp_path):
        """Calling start() twice must not relaunch the browser."""
        _module, pw_instance, *_ = fake_playwright
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        bm.start("http://example.com")
        bm.start("http://example.com")

        assert pw_instance.chromium.launch.call_count == 1
        bm.close()

    def test_capture_vulnerability_auto_starts(self, fake_playwright, tmp_path):
        """A caller that never calls start() explicitly still gets a
        working capture (auto-start on first use)."""
        _module, pw_instance, _browser, _context, page = fake_playwright
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability(
            "path_traversal",
            "http://example.com/?item=../../../../etc/passwd",
            payload="../../../../etc/passwd",
            note="LFI/Path Traversal Confirmed",
        )

        assert pw_instance.chromium.launch.call_count == 1
        assert evidence["vulnerability_type"] == "path_traversal"
        assert evidence["payload"] == "../../../../etc/passwd"
        assert evidence["note"] == "LFI/Path Traversal Confirmed"
        assert evidence["screenshot_path"].startswith(str(tmp_path))
        assert evidence["screenshot_path"].endswith(".png")
        page.goto.assert_called_once()
        page.screenshot.assert_called_once()
        bm.close()

    def test_close_is_idempotent(self, fake_playwright, tmp_path):
        bm = BrowserManager(screenshot_dir=str(tmp_path))
        bm.start("http://example.com")

        bm.close()
        bm.close()  # must not raise

        assert bm.is_started is False

    def test_close_without_start_does_not_raise(self, tmp_path):
        bm = BrowserManager(screenshot_dir=str(tmp_path))
        bm.close()  # must not raise

    def test_context_manager_starts_and_closes(self, fake_playwright, tmp_path):
        _module, pw_instance, *_ = fake_playwright
        with BrowserManager(screenshot_dir=str(tmp_path)) as bm:
            bm.capture_vulnerability("path_traversal", "http://example.com/?item=web.config")
            assert bm.is_started is True

        assert bm.is_started is False


class TestBrowserManagerErrors:
    def test_missing_playwright_package_raises_actionable_error(self, tmp_path):
        """NFR-003: a missing `playwright` install must surface a specific,
        actionable error, not a raw ImportError traceback."""
        with patch.dict(sys.modules, {"playwright.sync_api": None, "playwright": None}):
            bm = BrowserManager(screenshot_dir=str(tmp_path))
            with pytest.raises(BrowserManagerError, match="Playwright is not installed"):
                bm.start("http://example.com")

    def test_screenshot_failure_raises_browser_manager_error(self, fake_playwright, tmp_path):
        _module, _pw_instance, _browser, _context, page = fake_playwright
        page.screenshot.side_effect = RuntimeError("boom")
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        with pytest.raises(BrowserManagerError, match="Screenshot capture failed"):
            bm.capture_vulnerability("path_traversal", "http://example.com/?item=web.config")

        bm.close()
