from unittest.mock import MagicMock

import pytest

from app.tools.crawler import CrawlerService

pytestmark = pytest.mark.unit


class TestCrawlTarget:
    def test_bounds_curl_with_a_timeout(self):
        """Regression test: crawl_target had no explicit curl timeout - a
        live check against a real, currently-down practice site during
        specs/018 CHK090's own verification showed this would otherwise
        block on command_runner.py's much longer generic default timeout
        instead of failing fast."""
        runner = MagicMock()
        runner.run.return_value = ""
        memory = MagicMock()
        svc = CrawlerService(runner, memory)

        svc.crawl_target("http://example.com")

        cmd = runner.run.call_args[0][0]
        assert "--max-time" in cmd
        assert "--connect-timeout" in cmd

    def test_parses_discovered_links(self):
        """Verify Parses discovered links."""
        # runner.run() returns the full shell pipeline's output (after
        # `cut -d'"' -f2`), i.e. bare URLs - not the raw `href="..."`
        # matches grep alone would produce.
        runner = MagicMock()
        runner.run.return_value = "/about\n/contact\njavascript:void(0)"
        memory = MagicMock()
        svc = CrawlerService(runner, memory)

        result = svc.crawl_target("http://example.com")

        assert "/about" in result
        assert "/contact" in result
        assert "javascript:void(0)" not in result

    def test_empty_response_reports_zero_links(self):
        """Verify Empty response reports zero links."""
        runner = MagicMock()
        runner.run.return_value = ""
        memory = MagicMock()
        svc = CrawlerService(runner, memory)

        result = svc.crawl_target("http://example.com")

        assert "Found 0 links" in result
