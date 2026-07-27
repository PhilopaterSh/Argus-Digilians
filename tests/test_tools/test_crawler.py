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


class TestSrcExtraction:
    """Regression: the crawler only extracted `href="..."`, which structurally
    misses the endpoints traversal/LFI sinks most often sit behind. PortSwigger's
    "File path traversal, simple case" exposes its vulnerable `/image?filename=`
    solely in an `<img src>`, so an href-only crawl reported "Found 0 links" and
    PathTraversalScanner inherited no attack surface from memory.
    """

    def test_extraction_pattern_covers_src_as_well_as_href(self):
        """The curl pipeline must grep for both attributes."""
        runner = MagicMock()
        runner.run.return_value = ""
        svc = CrawlerService(runner, MagicMock())

        svc.crawl_target("http://example.com")

        cmd = runner.run.call_args[0][0]
        assert "(href|src)=" in cmd, f"src= not extracted: {cmd}"

    def test_img_src_endpoint_is_recorded_as_a_link(self):
        """An `<img src>` endpoint must reach memory so the traversal scanner
        can pick it up as an injection point."""
        runner = MagicMock()
        # Simulates the shell pipeline's output for a page whose only
        # parameter-bearing endpoint is an image tag.
        runner.run.return_value = "/image?filename=23.jpg\n/product?productId=1\n"
        memory = MagicMock()
        svc = CrawlerService(runner, memory)

        report = svc.crawl_target("http://example.com")

        recorded = [c.args[3] for c in memory.add_finding.call_args_list]
        assert "/image?filename=23.jpg" in recorded
        assert "Found 2 links" in report

    def test_target_url_is_shell_quoted(self):
        """The URL is interpolated into a shell pipeline; it must be quoted."""
        runner = MagicMock()
        runner.run.return_value = ""
        svc = CrawlerService(runner, MagicMock())

        svc.crawl_target("http://example.com/a'b")

        cmd = runner.run.call_args[0][0]
        assert "'\"'\"'" in cmd, f"URL not shell-quoted: {cmd}"
