from unittest.mock import MagicMock, patch

import pytest

from app.tools.evasion import EvasionService

pytestmark = pytest.mark.unit


def _make_runner(response_map: dict, default: str = ""):
    """Build a mock CommandRunner whose `.run()` reply depends on which
    payload substring appears in the command - so tests don't depend on
    `advanced_vuln_probe`'s internal payload iteration order.

    `shuf` (PayloadsAllTheThings Intruder/ wordlist sampling, see
    `fetch_intruder_payloads`) always returns empty by default - as if no
    local mirror were present - so existing tests get the same deterministic
    payload set as before that enrichment existed, unless a test explicitly
    overrides it via `response_map`.

    Args:
        response_map (dict): Maps a command substring to the canned
            response returned when a run() call's command contains it.
        default (str): Returned when no substring in `response_map`
            matches and the command isn't a `shuf` call.

    Returns:
        MagicMock: A mock CommandRunner with `.run` wired to the behavior
        above.
    """

    def run(command, timeout=None):
        """Return the canned response for the first matching substring, else the default.

        Args:
            command (str): The command string being "run".
            timeout: Currently unused - accepted for call-site
                compatibility with the real `CommandRunner.run`.

        Returns:
            str: The matching `response_map` value, `""` for a `shuf`
            command with no match, or `default` otherwise.
        """
        for substr, response in response_map.items():
            if substr in command:
                return response
        if command.startswith("shuf"):
            return ""
        return default

    mock = MagicMock()
    mock.run.side_effect = run
    return mock


class TestAdvancedVulnProbe:
    @patch("app.tools.evasion.time.sleep")
    def test_bounds_every_curl_call_with_a_timeout(self, _mock_sleep):
        """Verify Bounds every curl call with a timeout.
        
        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({})
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        svc.advanced_vuln_probe("http://example.com")

        curl_calls = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert len(curl_calls) > 0
        for cmd in curl_calls:
            assert "--max-time" in cmd
            assert "--connect-timeout" in cmd

    @patch("app.tools.evasion.time.sleep")
    def test_reports_clean_when_no_indicators_found(self, _mock_sleep):
        """Verify Reports clean when no indicators found.
        
        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({}, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "No vulnerabilities detected" in result
        memory.add_finding.assert_not_called()

    @patch("app.tools.evasion.time.sleep")
    def test_detects_linux_path_traversal_via_content_signature(self, _mock_sleep):
        """Regression: the original check only tried Windows' web.config and
        only looked at HTTP status (200 = success) - real content proof of a
        genuine /etc/passwd read (the payload most real-world and
        training-lab traversal vulnerabilities, e.g. PortSwigger's, actually
        test for) was never checked.
        
        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({
            "etc/passwd": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:...",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Path Traversal Success" in result
        assert "/etc/passwd read success" in result
        memory.add_finding.assert_any_call(
            "example.com", "evasion_probe", "vulnerability",
            "Traversal: ../../../../etc/passwd",
            "LFI/Path Traversal Confirmed (/etc/passwd read success)",
        )

    @patch("app.tools.evasion.time.sleep")
    def test_detects_linux_path_traversal_with_non_x_password_field(self, _mock_sleep):
        """Live-discovered 2026-08-02: SENSITIVE_CONTENT_INDICATORS' exact
        substring "root:x:0:0:" only matches when /etc/passwd's password
        field is the literal "x". A target whose root entry uses "*"
        instead (a real, common variant) produced genuine traversal
        evidence that the exact-substring check silently missed - fixed by
        find_sensitive_content_match()'s regex fallback in app/tools/utils.py.

        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({
            "etc/passwd": "root:*:0:0:root:/root:/bin/bash\ndaemon:x:1:1:...",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Path Traversal Success" in result
        assert "/etc/passwd read success" in result

    @patch("app.tools.evasion.time.sleep")
    def test_tries_linux_traversal_payloads_not_only_windows(self, _mock_sleep):
        """Verify Tries linux traversal payloads not only windows.
        
        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({})
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        svc.advanced_vuln_probe("http://example.com")

        commands = [call[0][0] for call in runner.run.call_args_list]
        assert any("etc/passwd" in cmd or "etc%2fpasswd" in cmd for cmd in commands)
        assert any("web.config" in cmd for cmd in commands)

    @patch("app.tools.evasion.time.sleep")
    def test_detects_sqli_via_500_status(self, _mock_sleep):
        """Verify Detects sqli via 500 status.
        
        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({
            "1%20OR%201=1": "\n500",
        }, default="<html>OK</html>\n200")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Potential SQLi" in result
        assert "Server Error 500" in result
        memory.add_finding.assert_any_call(
            "example.com", "evasion_probe", "vulnerability",
            "SQLi: 1%20OR%201=1", "SQLi potential via WAF evasion",
        )

    @patch("app.tools.evasion.time.sleep")
    def test_detects_sqli_via_body_error_signature_without_500(self, _mock_sleep):
        """New capability: a target that returns 200 with a visible DB error
        in the body (instead of a 500) is now caught too - the original
        check only ever looked at the HTTP status code.
        
        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({
            "1%20OR%201=1": "You have an error in your SQL syntax; check the manual\n200",
        }, default="<html>OK</html>\n200")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Potential SQLi" in result
        assert "SQL error signature in response body" in result

    @patch("app.tools.evasion.time.sleep")
    def test_enriches_traversal_payloads_from_payloads_all_the_things(self, _mock_sleep):
        """New: advanced_vuln_probe() no longer relies solely on its own
        small static list - it samples a few real payloads from the local
        PayloadsAllTheThings mirror's Intruder/ wordlist (see
        app/tools/payloads.py::fetch_intruder_payloads) and probes those
        too.
        
        Args:
            _mock_sleep: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        runner = _make_runner({
            "shuf -n 4": "custom/traversal/payload\n",
            "custom/traversal/payload": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        commands = [call[0][0] for call in runner.run.call_args_list]
        assert any("custom/traversal/payload" in cmd for cmd in commands)
        assert "Path Traversal Success" in result


class TestAdvancedVulnProbeParameterFuzzingAndUrlCleaning:
    """2026-07-25 regression, found by directly testing advanced_vuln_probe()
    against this project's own specs/025 benchmark fixture
    (benchmarks/fixtures/path_traversal_download) and a live PortSwigger run
    log the same day - two real, confirmed gaps, not hypothetical ones."""

    @patch("app.tools.evasion.time.sleep")
    def test_strips_free_text_the_model_appended_after_the_url(self, _mock_sleep):
        """Live-observed: a real run called this tool with tool_input
        "https://<lab>.web-security-academy.net/ path traversal" - the
        model's own descriptive text appended after the URL. Un-sanitized,
        this produced a curl command targeting a broken URL (an embedded
        literal space, then trailing garbage), guaranteeing every probe
        failed regardless of the target's actual vulnerability."""
        runner = _make_runner({
            "etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com path traversal")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert commands, "no curl commands were issued"
        for cmd in commands:
            assert "path traversal" not in cmd, f"trailing free text leaked into a probe command: {cmd}"
            assert "http://example.com?" in cmd
        assert "Path Traversal Success" in result

    @patch("app.tools.evasion.time.sleep")
    def test_reuses_existing_query_parameter_name_instead_of_item(self, _mock_sleep):
        """A URL that already carries a discovered query parameter (e.g.
        crawled as "?filename=x.jpg") is a far stronger signal than any
        guess - the probe must reuse that exact parameter name for every
        payload rather than always trying the synthetic "item" first."""
        runner = _make_runner({
            "filename=../../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com/download?filename=welcome.txt")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert all("?item=" not in cmd for cmd in commands), \
            "should reuse the discovered 'filename' parameter, not fall back to 'item'"
        assert any("?filename=" in cmd for cmd in commands)
        assert "Path Traversal Success" in result

    @patch("app.tools.evasion.time.sleep")
    def test_falls_back_to_common_parameter_names_when_item_does_not_hit(self, _mock_sleep):
        """2026-07-25: this project's own specs/025 benchmark fixture
        (path_traversal_download) uses "?file=", not "?item=" - confirmed
        by directly testing this method against the fixture's real server,
        and by the fixture scoring 0% on its "traverse_to_secret_file"/
        "retrieve_flag" subtasks in every recorded benchmark run because of
        exactly this mismatch. A bare URL (no existing query string) must
        not stop at "item" - it should keep trying other common real-world
        parameter names until one produces a signal."""
        runner = _make_runner({
            "file=../../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com/download")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert any("?item=" in cmd for cmd in commands), "item should still be tried first"
        assert any("?file=" in cmd for cmd in commands), "file should be tried as a fallback candidate"
        assert "Path Traversal Success" in result

    @patch("app.tools.evasion.time.sleep")
    def test_stops_fuzzing_parameter_names_once_one_is_confirmed(self, _mock_sleep):
        """Once a parameter name is confirmed working for one payload, it
        should be reused directly for subsequent payloads instead of
        re-fuzzing item/file/filename/path/document every time - otherwise
        the fix would multiply request volume far more than necessary."""
        runner = _make_runner({
            "file=": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        svc.advanced_vuln_probe("http://example.com/download")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        # Every payload after the first hit should go straight to "file" -
        # "item" should only appear once per payload at most until the
        # first hit, never repeatedly probed once confirmed.
        item_attempts = sum(1 for cmd in commands if "?item=" in cmd)
        assert item_attempts == 1, f"expected exactly 1 'item' attempt (before confirmation), got {item_attempts}"


class TestAdvancedVulnProbeEndpointDiscovery:
    """specs/030, 2026-08-01: a bare-root probe that finds nothing used to
    just report clean - even though PortSwigger's own path-traversal labs
    put the real vulnerable parameter on a specific page (e.g.
    "/image?filename=..."), not on "/" itself. Live runs (b84499b0,
    5f71e301, others) called Advanced_Evasion_Probe against the bare root
    3 times, found nothing every time, and the model never called
    Crawl_Target first. These tests cover the discovery fallback that now
    kicks in when the root probe comes up empty."""

    @patch("app.tools.evasion.time.sleep")
    def test_finds_vulnerability_at_discovered_endpoint_when_root_is_clean(self, _mock_sleep):
        """The root page itself has nothing, but links to a page that
        does - the fallback must discover and probe it."""
        runner = _make_runner({
            "-L --max-time 10 --connect-timeout 5 'http://example.com'": "/image?filename=cat.jpg\n/about",
            "/image?filename=../../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Path Traversal Success" in result
        memory.add_finding.assert_any_call(
            "example.com", "evasion_probe", "vulnerability",
            "Traversal: ../../../../etc/passwd",
            "LFI/Path Traversal Confirmed (/etc/passwd read success)",
        )
        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert any("/image?filename=" in cmd for cmd in commands), \
            "should have probed the discovered /image?filename= endpoint, not just the root"

    @patch("app.tools.evasion.time.sleep")
    def test_reports_clean_when_root_and_discovered_endpoints_are_both_clean(self, _mock_sleep):
        """No regression for a genuinely clean target: discovery runs (the
        root probe found nothing), finds a link, probes it too, and still
        correctly reports clean when nothing hits anywhere."""
        runner = _make_runner({
            "-L --max-time 10 --connect-timeout 5 'http://example.com'": "/about\n/contact",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "No vulnerabilities detected" in result
        memory.add_finding.assert_not_called()

    @patch("app.tools.evasion.time.sleep")
    def test_skips_discovery_when_url_already_has_a_query_parameter(self, _mock_sleep):
        """A URL that already carries a query parameter is already a
        specific-enough target (e.g. crawled or user-supplied) - discovery
        must not fire even if that exact parameter doesn't hit, to avoid
        multiplying request volume for no reason."""
        runner = _make_runner({}, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        svc.advanced_vuln_probe("http://example.com/download?filename=welcome.txt")

        commands = [call[0][0] for call in runner.run.call_args_list]
        assert not any("-L --max-time 10" in cmd for cmd in commands), \
            "discovery should not run when the URL already has a query parameter"

    @patch("app.tools.evasion.time.sleep")
    def test_skips_discovery_when_root_probe_already_found_something(self, _mock_sleep):
        """No wasted discovery call when the root probe itself already
        confirmed a hit."""
        runner = _make_runner({
            "etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        svc.advanced_vuln_probe("http://example.com")

        commands = [call[0][0] for call in runner.run.call_args_list]
        assert not any("-L --max-time 10" in cmd for cmd in commands), \
            "discovery should not run when the root probe already found a vulnerability"

    @patch("app.tools.evasion.time.sleep")
    def test_finds_vulnerability_via_img_src_not_only_a_href(self, _mock_sleep):
        """2026-08-01: PortSwigger's own "File path traversal, simple case"
        lab loads its vulnerable endpoint as <img src="/image?filename=..."> -
        an src= attribute, not an href= link. Discovery must catch this,
        not just <a href> navigation links."""
        runner = _make_runner({
            "-L --max-time 10 --connect-timeout 5 'http://example.com'": "/image?filename=61.jpg",
            "/image?filename=../../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Path Traversal Success" in result
        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert any("/image?filename=" in cmd for cmd in commands)
        discovery_cmd = next(cmd for cmd in commands if "grep -oE" in cmd)
        assert "(href|src)" in discovery_cmd, "discovery must grep for src= as well as href="

    @patch("app.tools.evasion.time.sleep")
    def test_discovery_ignores_javascript_and_mailto_links(self, _mock_sleep):
        """Non-navigable hrefs must never be turned into probe URLs."""
        runner = _make_runner({
            "-L --max-time 10 --connect-timeout 5 'http://example.com'":
                "javascript:void(0)\nmailto:admin@example.com\n#top",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert not any("javascript:" in cmd or "mailto:" in cmd for cmd in commands)
        assert "No vulnerabilities detected" in result


class TestAdvancedVulnProbeScreenshotEvidence:
    """specs/029-vulnerability-screenshot-evidence: EvasionService's optional
    browser_manager argument. browser_manager=None (every test above) must
    keep behaving exactly as before - these tests cover the new,
    additive-only behavior when one is supplied."""

    @patch("app.tools.evasion.time.sleep")
    def test_captures_screenshot_on_confirmed_path_traversal(self, _mock_sleep):
        """2026-08-01: this test previously did NOT mock
        VulnerabilityReportWriter, so its fake mocked evidence (a
        `screenshot_path` that was never actually captured) got written by
        the REAL report writer to a real `reports/vulnerability_report_*.json`
        file on disk every time the test suite ran - confirmed live: a
        genuine test-pollution artifact
        (`vulnerability_report_example.com_20260801_190808.json`) was found
        sitting in a real working copy's `reports/` folder, matching this
        test's mock data exactly, and was mistaken for real target
        evidence. Now mocked like
        test_includes_report_path_when_screenshot_captured below already
        does, so running this test never touches the filesystem."""
        runner = _make_runner({
            "etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        browser_manager = MagicMock()
        browser_manager.capture_vulnerability.return_value = {
            "vulnerability_type": "path_traversal",
            "url": "http://example.com?item=../../../../etc/passwd",
            "payload": "../../../../etc/passwd",
            "note": "LFI/Path Traversal Confirmed (/etc/passwd read success)",
            "screenshot_path": "artifacts/screenshots/path_traversal_example.com_20260725_000000_000000.png",
            "timestamp": "2026-07-25T00:00:00",
        }
        svc = EvasionService(runner, memory, browser_manager=browser_manager)

        with patch("app.tools.evasion.VulnerabilityReportWriter") as MockWriter:
            MockWriter.return_value.save_report.return_value = "reports/vulnerability_report_example.com_TESTFAKE.json"
            result = svc.advanced_vuln_probe("http://example.com")

        browser_manager.capture_vulnerability.assert_any_call(
            "path_traversal",
            "http://example.com?item=../../../../etc/passwd",
            payload="../../../../etc/passwd",
            note="LFI/Path Traversal Confirmed (/etc/passwd read success)",
        )
        assert "Screenshot saved" in result
        assert "path_traversal_example.com" in result
        MockWriter.return_value.save_report.assert_called_once()

    @patch("app.tools.evasion.time.sleep")
    def test_includes_report_path_when_screenshot_captured(self, _mock_sleep):
        runner = _make_runner({
            "etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        browser_manager = MagicMock()
        browser_manager.capture_vulnerability.return_value = {
            "vulnerability_type": "path_traversal",
            "url": "http://example.com?item=../../../../etc/passwd",
            "payload": "../../../../etc/passwd",
            "note": "note",
            "screenshot_path": "artifacts/screenshots/shot.png",
            "timestamp": "2026-07-25T00:00:00",
        }
        svc = EvasionService(runner, memory, browser_manager=browser_manager)

        with patch("app.tools.evasion.VulnerabilityReportWriter") as MockWriter:
            MockWriter.return_value.save_report.return_value = "reports/vulnerability_report_example.com_20260725_000000.json"
            result = svc.advanced_vuln_probe("http://example.com")

        assert "reports/vulnerability_report_example.com_20260725_000000.json" in result
        MockWriter.return_value.save_report.assert_called_once()
        args, _ = MockWriter.return_value.save_report.call_args
        assert args[0] == "example.com"
        assert args[1] == "path_traversal"
        # >=1 rather than a hardcoded count: several static traversal
        # payloads share the "etc/passwd" substring this mocked runner
        # matches on (e.g. "../../../../etc/passwd" and
        # "....//....//....//....//etc/passwd"), so more than one capture
        # can legitimately fire - the same multiplicity
        # test_detects_linux_path_traversal_via_content_signature already
        # tolerates via assert_any_call rather than an exact call count.
        assert len(args[2]) == browser_manager.capture_vulnerability.call_count
        assert len(args[2]) >= 1

    @patch("app.tools.evasion.time.sleep")
    def test_screenshot_capture_failure_does_not_break_finding(self, _mock_sleep):
        """FR-005: a browser/screenshot failure must never take down an
        already-confirmed, already-recorded text finding."""
        runner = _make_runner({
            "etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        browser_manager = MagicMock()
        browser_manager.capture_vulnerability.side_effect = RuntimeError("browser crashed")
        svc = EvasionService(runner, memory, browser_manager=browser_manager)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Path Traversal Success" in result
        assert "/etc/passwd read success" in result
        memory.add_finding.assert_any_call(
            "example.com", "evasion_probe", "vulnerability",
            "Traversal: ../../../../etc/passwd",
            "LFI/Path Traversal Confirmed (/etc/passwd read success)",
        )
        # The failure itself must be visible in the returned text (not just
        # a logger.warning() that's easy to miss depending on logging
        # config) - otherwise a broken Playwright install looks identical
        # to "target genuinely not vulnerable, nothing to report."
        assert "Screenshot capture FAILED" in result
        assert "browser crashed" in result

    @patch("app.tools.evasion.time.sleep")
    def test_no_report_written_when_no_screenshot_captured(self, _mock_sleep):
        """No browser_manager supplied (the default) - identical to every
        pre-existing test above, confirming zero regressions (SC-002)."""
        runner = _make_runner({
            "etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        }, default="<html>Not Found</html>")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        with patch("app.tools.evasion.VulnerabilityReportWriter") as MockWriter:
            result = svc.advanced_vuln_probe("http://example.com")

        MockWriter.return_value.save_report.assert_not_called()
        assert "[report]" not in result


class TestAdvancedVulnProbeSqliParameterFuzzing:
    """2026-08-23 live-run finding (agent run 1099dc95, a PortSwigger "SQL
    injection vulnerability in WHERE clause" lab): the SQLi probe always
    hardcoded `?id={payload}`, so it silently tested the wrong parameter on
    a lab that used `?category=` - the agent then burned its whole budget
    on unrelated Recon_Suite/Advanced_Evasion_Probe retries because nothing
    was ever confirmed. Mirrors the parameter-fuzzing coverage
    TestAdvancedVulnProbeParameterFuzzingAndUrlCleaning already has for
    traversal."""

    @patch("app.tools.evasion.time.sleep")
    def test_reuses_existing_query_parameter_name_for_sqli_instead_of_id(self, _mock_sleep):
        """A URL that already carries a discovered query parameter (e.g.
        crawled as "?category=Gifts") is a far stronger signal than the
        "id" guess - the probe must reuse that exact parameter name."""
        runner = _make_runner({
            "category=1%20OR%201=1": "\n500",
        }, default="<html>OK</html>\n200")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com/filter?category=Gifts")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert not any("?id=" in cmd for cmd in commands), \
            "should reuse the discovered 'category' parameter, not fall back to 'id'"
        assert any("?category=" in cmd for cmd in commands)
        assert "Potential SQLi" in result

    @patch("app.tools.evasion.time.sleep")
    def test_falls_back_to_common_parameter_names_for_sqli_when_id_does_not_hit(self, _mock_sleep):
        """A bare URL (no existing query string) must not stop at "id" -
        it should keep trying other common real-world SQLi parameter
        names (e.g. PortSwigger's own "category") until one hits."""
        runner = _make_runner({
            "category=1%20OR%201=1": "\n500",
        }, default="<html>OK</html>\n200")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        result = svc.advanced_vuln_probe("http://example.com/filter")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert any("?id=" in cmd for cmd in commands), "id should still be tried first"
        assert any("?category=" in cmd for cmd in commands), "category should be tried as a fallback candidate"
        assert "Potential SQLi" in result

    @patch("app.tools.evasion.time.sleep")
    def test_does_not_produce_a_double_question_mark_when_url_has_existing_query(self, _mock_sleep):
        """2026-08-23: appending "?id=..." to a URL that already had its
        own query string produced an invalid double-"?" URL that could
        never succeed regardless of whether the target was vulnerable."""
        runner = _make_runner({}, default="<html>OK</html>\n200")
        memory = MagicMock()
        svc = EvasionService(runner, memory)

        svc.advanced_vuln_probe("http://example.com/filter?category=Gifts")

        commands = [call[0][0] for call in runner.run.call_args_list if call[0][0].startswith("curl")]
        assert commands, "no curl commands were issued"
        for cmd in commands:
            assert cmd.count("?") <= 1, f"double question mark in probe URL: {cmd}"


class TestAdvancedVulnProbeSqliScreenshotEvidence:
    """2026-08-23: a confirmed SQLi previously never triggered a
    screenshot at all - only _probe_traversal_target had that wiring.
    These mirror TestAdvancedVulnProbeScreenshotEvidence's traversal
    coverage for the SQLi path."""

    @patch("app.tools.evasion.time.sleep")
    def test_captures_screenshot_on_confirmed_sqli(self, _mock_sleep):
        runner = _make_runner({
            "1%20OR%201=1": "\n500",
        }, default="<html>OK</html>\n200")
        memory = MagicMock()
        browser_manager = MagicMock()
        browser_manager.capture_vulnerability.return_value = {
            "vulnerability_type": "sql_injection",
            "url": "http://example.com?id=1%20OR%201=1",
            "payload": "1%20OR%201=1",
            "note": "SQLi potential via WAF evasion",
            "screenshot_path": "artifacts/screenshots/sql_injection_example.com_20260823_000000_000000.png",
            "timestamp": "2026-08-23T00:00:00",
        }
        svc = EvasionService(runner, memory, browser_manager=browser_manager)

        with patch("app.tools.evasion.VulnerabilityReportWriter") as MockWriter:
            MockWriter.return_value.save_report.return_value = "reports/vulnerability_report_example.com_TESTFAKE.json"
            result = svc.advanced_vuln_probe("http://example.com")

        browser_manager.capture_vulnerability.assert_any_call(
            "sql_injection",
            "http://example.com?id=1%20OR%201=1",
            payload="1%20OR%201=1",
            note="SQLi potential via WAF evasion",
        )
        assert "Screenshot saved" in result
        assert "sql_injection_example.com" in result

    @patch("app.tools.evasion.time.sleep")
    def test_report_type_reflects_sqli_when_only_sqli_confirmed(self, _mock_sleep):
        """The report-writer call must describe what was actually
        captured, not a hardcoded "path_traversal" left over from before
        SQLi had screenshot capture at all."""
        runner = _make_runner({
            "1%20OR%201=1": "\n500",
        }, default="<html>OK</html>\n200")
        memory = MagicMock()
        browser_manager = MagicMock()
        browser_manager.capture_vulnerability.return_value = {
            "vulnerability_type": "sql_injection",
            "url": "http://example.com?id=1%20OR%201=1",
            "payload": "1%20OR%201=1",
            "note": "note",
            "screenshot_path": "artifacts/screenshots/shot.png",
            "timestamp": "2026-08-23T00:00:00",
        }
        svc = EvasionService(runner, memory, browser_manager=browser_manager)

        with patch("app.tools.evasion.VulnerabilityReportWriter") as MockWriter:
            MockWriter.return_value.save_report.return_value = "reports/vulnerability_report_example.com_20260823_000000.json"
            svc.advanced_vuln_probe("http://example.com")

        args, _ = MockWriter.return_value.save_report.call_args
        assert args[1] == "sql_injection"

    @patch("app.tools.evasion.time.sleep")
    def test_sqli_screenshot_capture_failure_does_not_break_finding(self, _mock_sleep):
        """A browser/screenshot failure must never take down an
        already-confirmed, already-recorded SQLi text finding."""
        runner = _make_runner({
            "1%20OR%201=1": "\n500",
        }, default="<html>OK</html>\n200")
        memory = MagicMock()
        browser_manager = MagicMock()
        browser_manager.capture_vulnerability.side_effect = RuntimeError("browser crashed")
        svc = EvasionService(runner, memory, browser_manager=browser_manager)

        result = svc.advanced_vuln_probe("http://example.com")

        assert "Potential SQLi" in result
        assert "Screenshot capture FAILED" in result
        assert "browser crashed" in result
