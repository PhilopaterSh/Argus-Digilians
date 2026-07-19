from unittest.mock import MagicMock, patch

from app.tools.evasion import EvasionService


def _make_runner(response_map: dict, default: str = ""):
    """Build a mock CommandRunner whose `.run()` reply depends on which
    payload substring appears in the command - so tests don't depend on
    `advanced_vuln_probe`'s internal payload iteration order.

    `shuf` (PayloadsAllTheThings Intruder/ wordlist sampling, see
    `fetch_intruder_payloads`) always returns empty by default - as if no
    local mirror were present - so existing tests get the same deterministic
    payload set as before that enrichment existed, unless a test explicitly
    overrides it via `response_map`."""

    def run(command, timeout=None):
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
