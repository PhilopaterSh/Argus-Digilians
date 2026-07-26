from unittest.mock import MagicMock, patch

from app.tools.path_traversal import PathTraversalScanner


def _make_runner(response_map: dict, default: str = "<html>Not Found</html>"):
    """Mock CommandRunner whose `.run()` reply depends on which substring
    appears in the command, so tests don't couple to payload/param iteration
    order. `shuf` (PayloadsAllTheThings sampling) returns empty by default so
    the payload set is deterministic unless a test overrides it.
    """
    def run(command, timeout=None):
        # Wake probe (`_wait_until_awake`): status-only curl. Default to a
        # healthy 200 so the scan proceeds; a test forces a dead target via an
        # explicit 'http_code' key in response_map.
        if "-o /dev/null" in command and "http_code" in command:
            return response_map.get("http_code", "200")
        for substr, response in response_map.items():
            if substr in command:
                return response
        if command.startswith("shuf"):
            return ""
        return default

    mock = MagicMock()
    mock.run.side_effect = run
    return mock


def _memory_with_links(links=None):
    memory = MagicMock()
    memory.get_detailed_findings.return_value = [
        {"data_type": "link", "raw_data": link} for link in (links or [])
    ]
    return memory


class TestPathTraversalScan:
    @patch("app.tools.path_traversal.time.sleep")
    def test_confirms_etc_passwd_read_via_content_signature(self, _sleep):
        """A body containing the /etc/passwd signature is a confirmed finding,
        recorded in memory with the dedicated 'path_traversal' tool name."""
        runner = _make_runner({"etc/passwd": "root:x:0:0:root:/root:/bin/bash"})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com")

        assert "Path Traversal Success" in report
        assert "/etc/passwd read success" in report
        # Raw signature token embedded so the reflective verifier re-confirms.
        assert "[signature: root:x:0:0:]" in report
        assert memory.add_finding.called
        tool_names = {c.args[1] for c in memory.add_finding.call_args_list}
        assert "path_traversal" in tool_names

    @patch("app.tools.path_traversal.time.sleep")
    def test_reports_clean_when_no_signature_found(self, _sleep):
        runner = _make_runner({}, default="<html>Nothing here</html>")
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com")

        assert "No path-traversal vulnerabilities confirmed" in report
        memory.add_finding.assert_not_called()

    @patch("app.tools.path_traversal.time.sleep")
    def test_emits_multiple_encoding_variants(self, _sleep):
        """The encoding matrix must produce raw, single, and double URL-encoded
        forms of the same traversal, not just one representation."""
        runner = _make_runner({})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        svc.run_traversal_scan("http://example.com", params=["file"], max_probes=200)

        commands = [c.args[0] for c in runner.run.call_args_list]
        joined = "\n".join(commands)
        assert "../etc/passwd" in joined or "../../etc/passwd" in joined  # raw
        assert "..%2f" in joined      # single URL-encoded
        assert "..%252f" in joined    # double URL-encoded
        assert "....//" in joined     # collapse bypass

    @patch("app.tools.path_traversal.time.sleep")
    def test_hybrid_param_discovery_prefers_crawler_links(self, _sleep):
        """Parameter names mined from crawler-discovered links must be probed,
        ahead of the static fallback list."""
        runner = _make_runner({})
        memory = _memory_with_links(["http://example.com/view?report=1&x=2"])
        svc = PathTraversalScanner(runner, memory)

        svc.run_traversal_scan("http://example.com", max_probes=500)

        commands = "\n".join(c.args[0] for c in runner.run.call_args_list)
        assert "report=" in commands  # crawler-derived param used
        assert "x=" in commands

    @patch("app.tools.path_traversal.time.sleep")
    def test_windows_win_ini_signature_confirmed(self, _sleep):
        runner = _make_runner({
            "win.ini": "; for 16-bit app support\n[fonts]",
        })
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com")

        assert "win.ini read success" in report

    @patch("app.tools.path_traversal.time.sleep")
    def test_auto_discovers_vulnerable_endpoint_from_page_src(self, _sleep):
        """Key automated-flow capability: when handed only the site root (the
        agent's exploit node strips the path), the scanner fetches the root
        page, mines the '/image?filename=' endpoint out of an <img src>, and
        probes it - reproducing the PortSwigger file-path-traversal lab."""
        runner = _make_runner({
            # Root page fetch returns HTML whose image tag exposes the endpoint.
            "http://example.com/'": '<html><body><img src="/image?filename=23.jpg"></body></html>',
            # The traversal probe against that endpoint reads /etc/passwd.
            "/image?filename=../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash",
        })
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com")

        assert "Path Traversal Success" in report
        assert "endpoint=http://example.com/image" in report
        commands = "\n".join(c.args[0] for c in runner.run.call_args_list)
        assert "/image?filename=../../../etc/passwd" in commands
        memory.add_finding.assert_called()

    @patch("app.tools.path_traversal.time.sleep")
    def test_does_not_probe_external_hosts_from_page_links(self, _sleep):
        """In-scope guard: external links on the page (CDNs, social buttons)
        must never be probed with traversal payloads."""
        runner = _make_runner({
            "http://example.com/'": (
                '<html><a href="https://twitter.com/share?text=x">t</a>'
                '<img src="/image?filename=1.jpg"></html>'
            ),
        })
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        svc.run_traversal_scan("http://example.com", max_probes=500)

        commands = "\n".join(c.args[0] for c in runner.run.call_args_list)
        assert "twitter.com" not in commands
        assert "example.com/image" in commands

    @patch("app.tools.path_traversal.time.sleep")
    def test_respects_max_probes_ceiling(self, _sleep):
        runner = _make_runner({})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        svc.run_traversal_scan("http://example.com", params=["file"], max_probes=5)

        # Count only actual payload probes (contain the injected param), not
        # the wake/status or page-discovery curls.
        probe_calls = [c for c in runner.run.call_args_list if "file=" in c.args[0]]
        assert len(probe_calls) <= 5


class TestUnreachableTarget:
    @patch("app.tools.path_traversal.time.sleep")
    def test_dead_target_reports_unreachable_not_no_vuln(self, _sleep):
        """A target that only returns 504/000 must be reported as UNREACHABLE,
        distinct from a clean 'no vulnerability' result - and must not record
        any finding."""
        runner = _make_runner({"http_code": "504"})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("https://dead.example.com")

        assert "TARGET UNREACHABLE" in report
        assert "No path-traversal vulnerabilities confirmed" not in report
        memory.add_finding.assert_not_called()
