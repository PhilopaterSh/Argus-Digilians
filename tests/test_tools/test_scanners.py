import pytest
from unittest.mock import MagicMock

from app.tools.scanners import VulnerabilityScanners

pytestmark = pytest.mark.unit


@pytest.fixture
def service(tmp_path, monkeypatch):
    """Build a VulnerabilityScanners with mocked runner/memory, cwd'd into a temp dir.

    Args:
        tmp_path: test parameter provided by this test's own setup (a
            pytest fixture or a mock/patch injected via a decorator - see
            the test's parameters/decorators for which).
        monkeypatch: test parameter provided by this test's own setup (a
            pytest fixture or a mock/patch injected via a decorator - see
            the test's parameters/decorators for which).

    Returns:
        tuple: `(VulnerabilityScanners, MagicMock runner, MagicMock memory)`.
    """
    monkeypatch.chdir(tmp_path)
    runner = MagicMock()
    memory = MagicMock()
    return VulnerabilityScanners(runner, memory), runner, memory


class TestRunNikto:
    def test_success_on_first_scheme_does_not_retry(self, service):
        """Verify Success on first scheme does not retry.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.return_value = "+ Server: Apache\n+ /admin/: found"

        svc.run_nikto("http://example.com")

        assert runner.run.call_count == 1

    def test_retries_with_http_when_https_connection_fails(self, service):
        """Regression test: a live run against scanme.nmap.org called Nikto
        with https:// while Nmap had already shown only port 80/http was
        open (443 was closed) - Nikto silently failed to connect and the
        agent had no way to tell the difference from a clean empty scan.
        Nikto itself should try the other scheme before giving up.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.side_effect = [
            "+ [FAIL] Unable to connect to example.com:443.",
            "+ Server: Apache\n+ /admin/: found",
        ]

        result = svc.run_nikto("https://example.com")

        assert runner.run.call_count == 2
        second_cmd = runner.run.call_args_list[1].args[0]
        assert "http://example.com" in second_cmd
        assert "https://example.com" not in second_cmd
        assert "/admin/: found" in result

    def test_returns_original_failure_when_both_schemes_fail(self, service):
        """Verify Returns original failure when both schemes fail.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.side_effect = [
            "+ [FAIL] Unable to connect to example.com:443.",
            "+ [FAIL] Unable to connect to example.com:80.",
        ]

        result = svc.run_nikto("https://example.com")

        assert runner.run.call_count == 2
        assert "443" in result

    def test_no_fallback_without_a_recognised_scheme(self, service):
        """Verify No fallback without a recognised scheme.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.return_value = "+ [FAIL] Unable to connect."

        svc.run_nikto("example.com")

        assert runner.run.call_count == 1

    def test_output_path_has_no_double_extension(self, service):
        """Regression test: nikto's own `-Format txt -o <path>` appends `.txt`
        itself regardless of what the given path already ends in - passing an
        already-`.txt`-suffixed path produced real `.txt.txt` files on disk
        (confirmed in reports/nikto/) while the returned message kept citing
        the un-suffixed (wrong) path. The `-o` flag's argument must have no
        extension; the returned message's cited path must have exactly one.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.return_value = "+ Server: Apache"

        result = svc.run_nikto("http://example.com")

        cmd = runner.run.call_args_list[0].args[0]
        assert " -o reports/nikto/nikto_example.com_" in cmd
        assert ".txt" not in cmd.split(" -o ")[1]
        assert "Saved to reports/nikto/nikto_example.com_" in result
        assert ".txt.txt" not in result


class TestRunFfufDiscovery:
    def test_success_on_first_scheme_does_not_retry(self, service):
        """Verify Success on first scheme does not retry.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.return_value = "http://example.com/admin [Status: 200]"

        svc.run_ffuf_discovery("http://example.com")

        assert runner.run.call_count == 1

    def test_retries_with_http_when_https_finds_nothing(self, service):
        """Verify Retries with http when https finds nothing.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.side_effect = [
            "",
            "http://example.com/admin [Status: 200]",
        ]

        result = svc.run_ffuf_discovery("https://example.com")

        assert runner.run.call_count == 2
        second_cmd = runner.run.call_args_list[1].args[0]
        assert "http://example.com" in second_cmd
        assert "admin" in result

    def test_reports_no_paths_when_both_schemes_empty(self, service):
        """Verify Reports no paths when both schemes empty.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.side_effect = ["", ""]

        result = svc.run_ffuf_discovery("https://example.com")

        assert runner.run.call_count == 2
        assert "No notable paths" in result
