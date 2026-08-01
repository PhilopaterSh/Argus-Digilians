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


class TestAdvancedVulnProbeScreenshotEvidence:
    """specs/029-vulnerability-screenshot-evidence: EvasionService's optional
    browser_manager argument. browser_manager=None (every test above) must
    keep behaving exactly as before - these tests cover the new,
    additive-only behavior when one is supplied."""

    @patch("app.tools.evasion.time.sleep")
    def test_captures_screenshot_on_confirmed_path_traversal(self, _mock_sleep):
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

        result = svc.advanced_vuln_probe("http://example.com")

        browser_manager.capture_vulnerability.assert_any_call(
            "path_traversal",
            "http://example.com?item=../../../../etc/passwd",
            payload="../../../../etc/passwd",
            note="LFI/Path Traversal Confirmed (/etc/passwd read success)",
        )
        assert "Screenshot saved" in result
        assert "path_traversal_example.com" in result

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
