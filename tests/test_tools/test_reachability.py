import pytest
from unittest.mock import MagicMock

from app.tools.reachability import ReachabilityService

pytestmark = pytest.mark.unit


@pytest.fixture
def service():
    """Build a ReachabilityService with mocked runner/memory; yields (service, runner, memory).

    Returns:
        tuple: `(ReachabilityService, MagicMock runner, MagicMock memory)`.
    """
    runner = MagicMock()
    memory = MagicMock()
    return ReachabilityService(runner, memory), runner, memory


class TestCheckReachability:
    def test_strips_scheme_before_pinging(self, service):
        """Regression test: a live run against https://scanme.nmap.org passed
        the full URL straight to `ping`, which always fails with "Name or
        service not known" regardless of whether the host is actually up -
        `ping` needs a bare host, not a scheme-qualified URL. This misled the
        agent into reporting a live target as DOWN right before a real nmap
        scan (via Recon_Suite) found it up with open ports.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.return_value = "4 received"

        svc.check_reachability("https://scanme.nmap.org")

        runner.run.assert_called_once_with("ping -c 4 scanme.nmap.org")

    def test_strips_port_before_pinging(self, service):
        """Verify Strips port before pinging.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.return_value = "4 received"

        svc.check_reachability("http://example.com:8080")

        runner.run.assert_called_once_with("ping -c 4 example.com")

    def test_bare_domain_unchanged(self, service):
        """Verify Bare domain unchanged.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, _ = service
        runner.run.return_value = "4 received"

        svc.check_reachability("example.com")

        runner.run.assert_called_once_with("ping -c 4 example.com")

    def test_reachable_upserts_original_target_to_memory(self, service):
        """Verify Reachable upserts original target to memory.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, memory = service
        runner.run.return_value = "4 received"

        result = svc.check_reachability("https://example.com")

        memory.upsert_target.assert_called_once_with("https://example.com")
        assert "REACHABLE" in result

    def test_unreachable_does_not_upsert(self, service):
        """Verify Unreachable does not upsert.
        
        Args:
            service: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        svc, runner, memory = service
        runner.run.return_value = "0 received"

        result = svc.check_reachability("https://example.com")

        memory.upsert_target.assert_not_called()
        assert "DOWN or unreachable" in result

    def test_falls_back_to_http_when_icmp_is_blocked(self, service):
        """Regression: a live run against a real PortSwigger Web Security
        Academy lab reported DOWN purely because ping got no reply (100%
        packet loss) - the lab was actually live (curl independently
        confirmed HTTP 200), matching the same "WAF/CDN drops ICMP" root
        cause the 2026-07-07 CHANGELOG entry already fixed for
        recon_suite's nmap scan, but check_reachability had no such
        fallback of its own until now.

        Args:
            service: test parameter provided by this test's own setup (a
                pytest fixture or a mock/patch injected via a decorator -
                see the test's parameters/decorators for which).

        Returns:
            None
        """
        svc, runner, memory = service

        def run(command):
            """Fail ping, succeed curl over HTTP - simulates ICMP blocked but the host being live.

            Args:
                command (str): The command being "run".

            Returns:
                str: A canned ping/curl reply, or "" for anything else.
            """
            if command.startswith("ping"):
                return "0 received"
            if command.startswith("curl"):
                return "200"
            return ""

        runner.run.side_effect = run

        result = svc.check_reachability("https://lab.example.com")

        assert "REACHABLE" in result
        assert "ICMP blocked" in result
        memory.upsert_target.assert_called_once_with("https://lab.example.com")

    def test_tries_opposite_scheme_before_giving_up(self, service):
        """Verify Tries opposite scheme before giving up.

        Args:
            service: test parameter provided by this test's own setup (a
                pytest fixture or a mock/patch injected via a decorator -
                see the test's parameters/decorators for which).

        Returns:
            None
        """
        svc, runner, memory = service

        def run(command):
            """Fail ping and https curl, succeed http curl - the opposite-scheme fallback path.

            Args:
                command (str): The command being "run".

            Returns:
                str: A canned ping/curl reply, or "" for anything else.
            """
            if command.startswith("ping"):
                return "0 received"
            if command.startswith("curl") and "https://" in command:
                return "000"
            if command.startswith("curl") and "http://" in command:
                return "200"
            return ""

        runner.run.side_effect = run

        result = svc.check_reachability("https://lab.example.com")

        assert "REACHABLE" in result
        memory.upsert_target.assert_called_once()

    def test_still_reports_down_when_both_ping_and_http_fail(self, service):
        """Verify Still reports down when both ping and http fail.

        Args:
            service: test parameter provided by this test's own setup (a
                pytest fixture or a mock/patch injected via a decorator -
                see the test's parameters/decorators for which).

        Returns:
            None
        """
        svc, runner, memory = service

        def run(command):
            """Fail both ping and every curl scheme attempt.

            Args:
                command (str): The command being "run".

            Returns:
                str: A canned failing ping/curl reply, or "" for anything else.
            """
            if command.startswith("ping"):
                return "0 received"
            if command.startswith("curl"):
                return "000"
            return ""

        runner.run.side_effect = run

        result = svc.check_reachability("https://example.com")

        memory.upsert_target.assert_not_called()
        assert "DOWN or unreachable" in result
