from unittest.mock import MagicMock

import pytest

from app.tools.secrets import SecretAnalyzer

pytestmark = pytest.mark.unit


class TestAnalyzeSecrets:
    def test_bounds_curl_with_a_timeout(self):
        """Regression test: analyze_secrets had no explicit curl timeout -
        see tests/test_tools/test_crawler.py's identical regression test
        for the live-confirmed root cause (specs/018 CHK090)."""
        runner = MagicMock()
        runner.run.return_value = ""
        memory = MagicMock()
        svc = SecretAnalyzer(runner, memory)

        svc.analyze_secrets("http://example.com")

        cmd = runner.run.call_args[0][0]
        assert "--max-time" in cmd
        assert "--connect-timeout" in cmd

    def test_reports_clean_when_no_secrets_found(self):
        """Verify Reports clean when no secrets found."""
        runner = MagicMock()
        runner.run.return_value = "<html><body>Hello world</body></html>"
        memory = MagicMock()
        svc = SecretAnalyzer(runner, memory)

        result = svc.analyze_secrets("http://example.com")

        assert "No obvious secrets" in result
        memory.add_finding.assert_not_called()

    def test_detects_aws_access_key(self):
        """Verify Detects aws access key."""
        # Plain (not "key: '...'"-wrapped) so only the AWS-specific pattern
        # matches, not also the Generic API Key pattern.
        runner = MagicMock()
        runner.run.return_value = "Some text mentioning AKIAABCDEFGHIJKLMNOP in passing."
        memory = MagicMock()
        svc = SecretAnalyzer(runner, memory)

        result = svc.analyze_secrets("http://example.com")

        assert "AWS Access Key" in result
        assert "AKIAABCDEFGHIJKLMNOP" in result
        memory.add_finding.assert_called_once()

    def test_detects_multiple_overlapping_patterns_on_the_same_value(self):
        """A value matching more than one pattern (e.g. an AWS key also
        embedded as "key: '...'") is recorded once per matching pattern -
        more signal, not a bug, but worth locking in explicitly."""
        runner = MagicMock()
        runner.run.return_value = "var config = { key: 'AKIAABCDEFGHIJKLMNOP' };"
        memory = MagicMock()
        svc = SecretAnalyzer(runner, memory)

        result = svc.analyze_secrets("http://example.com")

        assert "AWS Access Key" in result
        assert "Generic API Key" in result
        assert memory.add_finding.call_count == 2
