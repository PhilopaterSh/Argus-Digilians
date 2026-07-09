import pytest
from unittest.mock import MagicMock

from app.tools.reachability import ReachabilityService


@pytest.fixture
def service():
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
        scan (via Recon_Suite) found it up with open ports."""
        svc, runner, _ = service
        runner.run.return_value = "4 received"

        svc.check_reachability("https://scanme.nmap.org")

        runner.run.assert_called_once_with("ping -c 4 scanme.nmap.org")

    def test_strips_port_before_pinging(self, service):
        svc, runner, _ = service
        runner.run.return_value = "4 received"

        svc.check_reachability("http://example.com:8080")

        runner.run.assert_called_once_with("ping -c 4 example.com")

    def test_bare_domain_unchanged(self, service):
        svc, runner, _ = service
        runner.run.return_value = "4 received"

        svc.check_reachability("example.com")

        runner.run.assert_called_once_with("ping -c 4 example.com")

    def test_reachable_upserts_original_target_to_memory(self, service):
        svc, runner, memory = service
        runner.run.return_value = "4 received"

        result = svc.check_reachability("https://example.com")

        memory.upsert_target.assert_called_once_with("https://example.com")
        assert "REACHABLE" in result

    def test_unreachable_does_not_upsert(self, service):
        svc, runner, memory = service
        runner.run.return_value = "0 received"

        result = svc.check_reachability("https://example.com")

        memory.upsert_target.assert_not_called()
        assert "DOWN or unreachable" in result
