import sys
import os
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


def _response(status=200, content_type="text/html; charset=utf-8", body=b"<h1>ok</h1>"):
    """A fake Playwright Response for the page.goto() return value."""
    resp = MagicMock(name="response")
    resp.status = status
    resp.headers = {"content-type": content_type}
    resp.body.return_value = body
    return resp


PASSWD = (
    b"root:x:0:0:root:/root:/bin/bash\n"
    b"daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
)

# Every capture walks three browser steps - the site's landing page, the
# payload URL, then view-source: of that same URL - and photographs each.
GOTOS_PER_CAPTURE = 3
SHOTS_PER_CAPTURE = 3


def _writes_files(page):
    """Make the mocked page.screenshot() actually create its file, so code
    that checks a screenshot exists on disk behaves as it does for real."""
    def _write(path, **_kwargs):
        with open(path, "wb") as fh:
            fh.write(b"\x89PNG")
    page.screenshot.side_effect = _write


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
        assert page.goto.call_count == 2 * GOTOS_PER_CAPTURE
        assert page.screenshot.call_count == 2 * SHOTS_PER_CAPTURE
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
        assert page.goto.call_count == GOTOS_PER_CAPTURE
        assert page.screenshot.call_count == SHOTS_PER_CAPTURE
        bm.close()

    def test_capture_walks_three_browser_steps(self, fake_playwright, tmp_path):
        """Each finding is a walk-through: the site, the payload URL, and
        Chromium's own view-source of the raw response."""
        _module, _pw, _browser, _context, page = fake_playwright
        page.goto.return_value = _response(body=b"<pre>root:x:0:0</pre>")
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability("path_traversal", "http://example.com/view")

        assert "site_example.com_" in evidence["site_screenshot_path"]
        assert evidence["exploit_screenshot_path"].endswith("_exploit.png")
        assert evidence["response_screenshot_path"].endswith("_response.png")
        assert [s["step"] for s in evidence["steps"]] == [1, 2, 3]
        assert [s["url"] for s in evidence["steps"]] == [
            "http://example.com/",
            "http://example.com/view",
            "view-source:http://example.com/view",
        ]
        assert evidence["screenshots"] == [
            evidence["site_screenshot_path"],
            evidence["exploit_screenshot_path"],
            evidence["response_screenshot_path"],
        ]
        # All three were actually written, to three distinct paths.
        written = [call.kwargs["path"] for call in page.screenshot.call_args_list]
        assert written == evidence["screenshots"]
        bm.close()

    def test_nothing_is_drawn_by_argus(self, fake_playwright, tmp_path):
        """Every screenshot must be Chromium rendering a real server
        response - never markup this project composed itself."""
        _module, _pw, _browser, _context, page = fake_playwright
        page.goto.return_value = _response(content_type="image/jpeg", body=PASSWD)
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        bm.capture_vulnerability("path_traversal", "http://example.com/image")

        page.set_content.assert_not_called()
        # Only real navigations: the site, the payload URL, view-source.
        assert all(
            call.args[0].startswith(("http://", "https://", "view-source:"))
            for call in page.goto.call_args_list
        )
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


class TestSiteContextCapture:
    """The finding URL is often a sub-resource (`/image?filename=...`), whose
    screenshot shows no website at all. The site's own landing page is
    photographed separately so the report shows what was tested."""

    def test_navigates_to_the_origin_root_not_the_payload_url(self, fake_playwright, tmp_path):
        _module, _pw, _browser, _context, page = fake_playwright
        bm = BrowserManager(screenshot_dir=str(tmp_path)).start()

        path = bm.capture_site_context("http://example.com/image?filename=../../etc/passwd")

        assert path is not None
        page.goto.assert_called_once_with("http://example.com/", timeout=bm.nav_timeout_ms)
        assert page.screenshot.call_args.kwargs["path"] == path
        bm.close()

    def test_site_shot_is_taken_once_per_host(self, fake_playwright, tmp_path):
        """Three findings on one host must not mean three identical shots of
        the same landing page."""
        _module, _pw, _browser, _context, page = fake_playwright
        _writes_files(page)
        bm = BrowserManager(screenshot_dir=str(tmp_path)).start()

        first = bm.capture_site_context("http://example.com/a")
        second = bm.capture_site_context("http://example.com/b?x=1")

        assert first == second
        assert page.goto.call_count == 1
        assert page.screenshot.call_count == 1
        bm.close()

    def test_separate_hosts_get_separate_shots(self, fake_playwright, tmp_path):
        _module, _pw, _browser, _context, page = fake_playwright
        _writes_files(page)
        bm = BrowserManager(screenshot_dir=str(tmp_path)).start()

        first = bm.capture_site_context("http://example.com/a")
        second = bm.capture_site_context("http://other.test/a")

        assert first != second
        assert page.goto.call_count == 2
        bm.close()

    def test_unusable_url_returns_none(self, fake_playwright, tmp_path):
        _module, _pw, _browser, _context, page = fake_playwright
        bm = BrowserManager(screenshot_dir=str(tmp_path)).start()

        assert bm.capture_site_context("not-a-url") is None
        page.goto.assert_not_called()
        bm.close()

    def test_unreachable_site_does_not_break_the_finding(self, fake_playwright, tmp_path):
        """A landing page that will not load is context Argus can live
        without - the finding's own shots must still be captured."""
        _module, _pw, _browser, _context, page = fake_playwright
        page.goto.side_effect = [
            RuntimeError("site unreachable"),   # the landing page
            _response(content_type="image/jpeg", body=PASSWD),  # the payload URL
            _response(),                        # about:blank for the card
        ]
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability(
            "path_traversal", "http://example.com/image?filename=../../etc/passwd"
        )

        assert evidence["site_screenshot_path"] is None
        # 2026-08-23: the payload URL's response is non-renderable
        # (image/jpeg mislabeling text) and view-source succeeded, so the
        # useless broken-placeholder shot is discarded - only the
        # readable view-source screenshot remains (the site shot was
        # already unavailable).
        assert len(evidence["screenshots"]) == 1
        assert evidence["exploit_screenshot_path"] is None
        assert "root:x:0:0" in evidence["response_excerpt"]
        bm.close()


class TestPrimaryEvidenceSelection:
    """`capture_mode` records which step is the stronger proof.

    A path-traversal endpoint such as PortSwigger's `/image?filename=...`
    answers with an image Content-Type even when the traversal makes it
    return a text file. Chromium renders a broken-image placeholder at step
    2, so the readable proof is step 3's view-source shot.
    """

    def test_text_served_as_image_makes_view_source_primary(self, fake_playwright, tmp_path):
        _module, _pw, _browser, _context, page = fake_playwright
        page.goto.return_value = _response(content_type="image/jpeg", body=PASSWD)
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability(
            "path_traversal", "http://example.com/image?filename=../../etc/passwd"
        )

        assert evidence["capture_mode"] == "view_source"
        assert evidence["screenshot_path"] == evidence["response_screenshot_path"]
        assert evidence["http_status"] == 200
        assert evidence["content_type"] == "image/jpeg"
        assert "root:x:0:0" in evidence["response_excerpt"]
        bm.close()

    def test_broken_placeholder_screenshot_is_deleted_when_view_source_succeeds(self, fake_playwright, tmp_path):
        """2026-08-23 live-run finding: a server that mislabels a text
        response's Content-Type as an image (PortSwigger's own
        `/image?filename=...`) makes step 2's screenshot nothing but
        Chromium's broken-image placeholder - a near-solid-black frame
        that proves a request happened but shows no readable evidence.
        Once step 3's view-source shot has the real, readable proof, the
        useless placeholder must be removed from disk, not just
        unreferenced - otherwise it sits in artifacts/screenshots/ looking
        like a broken capture."""
        _module, _pw, _browser, _context, page = fake_playwright
        _writes_files(page)
        page.goto.return_value = _response(content_type="image/jpeg", body=PASSWD)
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability("path_traversal", "http://example.com/image")

        assert evidence["exploit_screenshot_path"] is None
        assert not any(
            step["action"].startswith("Requested the payload URL")
            for step in evidence["steps"]
        )
        assert evidence["response_screenshot_path"] is not None
        assert evidence["capture_mode"] == "view_source"
        # The file must actually be gone from disk, not just dropped from
        # the evidence dict.
        exploit_pngs = list(tmp_path.glob("*_exploit.png"))
        assert exploit_pngs == [], f"placeholder exploit screenshot should have been deleted, found: {exploit_pngs}"
        # The screenshots that ARE referenced must genuinely exist.
        for shot in evidence["screenshots"]:
            assert os.path.exists(shot)
        bm.close()

    def test_broken_placeholder_screenshot_is_kept_when_view_source_also_fails(self, fake_playwright, tmp_path):
        """If view-source itself fails, the placeholder must be kept as
        last-resort evidence that a request was made - deleting it too
        would leave the finding with no visual evidence at all for this
        step. No regression for test_view_source_failure_still_returns_the_finding's
        own scenario, made explicit here."""
        _module, _pw, _browser, _context, page = fake_playwright
        _writes_files(page)
        page.goto.side_effect = [
            _response(),                                        # site
            _response(content_type="image/jpeg", body=PASSWD),  # payload URL
            RuntimeError("view-source blocked"),                # step 3 fails
        ]
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability("path_traversal", "http://example.com/image")

        assert evidence["exploit_screenshot_path"] is not None
        assert os.path.exists(evidence["exploit_screenshot_path"])
        bm.close()

    def test_renderable_html_makes_the_exploit_shot_primary(self, fake_playwright, tmp_path):
        _module, _pw, _browser, _context, page = fake_playwright
        page.goto.return_value = _response(body=b"<pre>root:x:0:0</pre>")
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability(
            "path_traversal", "http://example.com/view?filename=../../etc/passwd"
        )

        assert evidence["capture_mode"] == "page"
        assert evidence["screenshot_path"] == evidence["exploit_screenshot_path"]
        # The body is still recorded, even though the page rendered fine.
        assert "root:x:0:0" in evidence["response_excerpt"]
        bm.close()

    def test_genuine_binary_image_makes_the_exploit_shot_primary(self, fake_playwright, tmp_path):
        """A real image renders as a real image - the browser's own view of
        it is the better evidence."""
        _module, _pw, _browser, _context, page = fake_playwright
        png_magic = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        page.goto.return_value = _response(content_type="image/png", body=png_magic)
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability("open_redirect", "http://example.com/logo.png")

        assert evidence["capture_mode"] == "page"
        assert evidence["screenshot_path"] == evidence["exploit_screenshot_path"]
        assert evidence["response_excerpt"] is None
        bm.close()

    def test_inspection_failure_keeps_the_exploit_shot_primary(self, fake_playwright, tmp_path):
        """If reading the response blows up, the capture must still succeed
        rather than losing the evidence entirely."""
        _module, _pw, _browser, _context, page = fake_playwright
        resp = _response(content_type="image/jpeg")
        resp.body.side_effect = RuntimeError("connection closed")
        page.goto.return_value = resp
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability("path_traversal", "http://example.com/image")

        assert evidence["capture_mode"] == "page"
        assert evidence["screenshot_path"] == evidence["exploit_screenshot_path"]
        bm.close()

    def test_view_source_failure_still_returns_the_finding(self, fake_playwright, tmp_path):
        """Step 3 is best-effort: if view-source will not load, the walk
        still comes back with steps 1 and 2."""
        _module, _pw, _browser, _context, page = fake_playwright
        page.goto.side_effect = [
            _response(),                                        # site
            _response(content_type="image/jpeg", body=PASSWD),  # payload URL
            RuntimeError("view-source blocked"),                # step 3
        ]
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        evidence = bm.capture_vulnerability("path_traversal", "http://example.com/image")

        assert evidence["response_screenshot_path"] is None
        assert [s["step"] for s in evidence["steps"]] == [1, 2]
        assert evidence["screenshot_path"] == evidence["exploit_screenshot_path"]
        assert evidence["capture_mode"] == "view_source"
        bm.close()


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

    def test_exploit_step_failure_raises(self, fake_playwright, tmp_path):
        """Step 2 is the finding itself - if the browser cannot reach the
        payload URL at all there is nothing to report."""
        _module, _pw, _browser, _context, page = fake_playwright
        page.goto.side_effect = [_response(), RuntimeError("net::ERR_FAILED")]
        bm = BrowserManager(screenshot_dir=str(tmp_path))

        with pytest.raises(BrowserManagerError, match="Screenshot capture failed"):
            bm.capture_vulnerability("path_traversal", "http://example.com/image")

        bm.close()
