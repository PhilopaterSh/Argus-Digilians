from unittest.mock import MagicMock, patch

import pytest

from app.tools.path_traversal import (
    PAYLOAD_LIMIT,
    PathTraversalScanner,
    _classify_payload,
    _payload_is_irregular,
    _payload_target_rank,
)


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


class TestShellInjectionHardening:
    """A hostile scan target must never be able to execute commands on the
    operator's own host via the probe strings this scanner builds.

    Attack path: `app/tools/crawler.py` mines links with
    `grep -oE 'href="[^"]+"' | cut -d'"' -f2`, which only excludes *double*
    quotes - so single quotes and shell metacharacters planted in a target's
    own `href` survive verbatim into ArgusMemory. `_discover_injection_points`
    then reads them back as injection points, and every probe is executed
    through a shell.
    """

    MALICIOUS_LINK = "/page' && touch /tmp/argus_pt_rce_canary && echo '?p=1"

    @patch("app.tools.path_traversal.time.sleep")
    def test_metacharacters_from_crawler_link_cannot_break_out_of_the_probe(self, _sleep, tmp_path):
        """The injected `&&` chain must stay inside a single quoted argv entry
        instead of becoming its own shell command.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
            tmp_path: pytest fixture; the canary is written here so the
                assertion never depends on a writable /tmp.
        """
        canary = tmp_path / "rce_canary"
        link = f"/page' && touch {canary} && echo '?p=1"
        captured = []

        class ShellRunner:
            """Executes for real, so a breakout would actually create the canary."""

            def run(self, command, timeout=None):
                captured.append(command)
                subprocess.run(command, shell=True, capture_output=True, timeout=10)
                return ""

        memory = MagicMock()
        memory.get_detailed_findings.return_value = [
            {"data_type": "link", "raw_data": link}
        ]
        svc = PathTraversalScanner(ShellRunner(), memory)

        point = next(
            (p for p in svc._discover_injection_points("http://127.0.0.1:1", None) if "&&" in p[0]),
            None,
        )
        assert point is not None, "test setup: malicious link should yield an injection point"
        svc._stealth_curl(point[0], point[1], "../etc/passwd")

        assert not canary.exists(), "shell breakout: target executed a command on the operator host"
        probe = captured[-1]
        # The metacharacters survive as literal text inside one quoted argument.
        assert "&& touch" in probe
        assert probe.rstrip().endswith("'")

    def test_quoted_probe_argument_is_a_single_argv_entry(self):
        """The full `url?param=payload` string must reach curl as exactly one
        argument, with embedded quotes neutralized rather than terminating it.
        """
        captured = []

        class Capture:
            def run(self, command, timeout=None):
                captured.append(command)
                return ""

        svc = PathTraversalScanner(Capture(), MagicMock())
        with patch("app.tools.path_traversal.time.sleep"):
            svc._stealth_curl("http://t.tld/a'b", "p", "../etc/passwd")

        # `sh -c` word-splitting must yield the URL intact as one token.
        argv = subprocess.run(
            ["sh", "-c", f'for a in {captured[0].split("connect-timeout 5 ", 1)[1]}; do echo "$a"; done'],
            capture_output=True, text=True,
        ).stdout.splitlines()
        assert "http://t.tld/a'b?p=../etc/passwd" in argv



class TestDeterminism:
    """The tiered attack-surface reporting and page-fetch retry tests this
    class originally covered were dropped along with the crawler attack-
    surface integration they depended on (superseded, see merge notes).
    This one test survives: it exercises the payload generator directly and
    has no dependency on that dropped feature.
    """


    @patch("app.tools.path_traversal.time.sleep")
    def test_mirror_enrichment_payloads_are_actually_probed(self, _sleep):
        """Regression: a hardcoded per-point budget of 60 truncated exactly the
        mirror-sampled payloads, which the generator appends past the built-in
        set, so PayloadsAllTheThings enrichment never fired.

        Mirror sampling belongs to `_generate_payloads()` - the fallback used
        when Payloads.db has not been built. In DB mode the wordlist itself is
        the enrichment, so this asserts against the generator directly.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({"shuf": "MIRROR_ONLY_PAYLOAD\n"})
        svc = PathTraversalScanner(runner, _memory_with_links())

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


class TestPayloadDatabaseSource:
    """Payloads now come from `Payloads/Payloads.db` via `payload_store.py`.
    The in-code generator survives only as a fallback for environments where
    that DB has not been built (it is gitignored), so both paths are covered.
    """

    @staticmethod
    def _db_available():
        """Whether Payloads.db exists and holds traversal rows.

        Returns:
            bool: True when the DB can be opened and has traversal payloads.
        """
        try:
            from Payloads.payload_store import PayloadStore
            store = PayloadStore()
            try:
                return store.count("traversal") > 0
            finally:
                store.close()
        except Exception:
            return False

    LAB_PAYLOADS = {
        "simple case": "../../../etc/passwd",
        "absolute path bypass": "/etc/passwd",
        "stripped non-recursively": "....//....//....//etc/passwd",
        "superfluous URL-decode": "..%252f..%252f..%252fetc%252fpasswd",
        "validation of start of path": "/var/www/images/../../../etc/passwd",
        "null byte bypass": "../../../etc/passwd%00.png",
    }

    def test_db_supplies_the_payloads_when_present(self):
        if not self._db_available():
            pytest.skip("Payloads.db not built")
        runner = MagicMock()
        runner.run.return_value = ""
        svc = PathTraversalScanner(runner, MagicMock())

        payloads = svc._build_payloads()

        # The generator emits exactly 94; a DB read is capped at PAYLOAD_LIMIT.
        assert len(payloads) == PAYLOAD_LIMIT
        assert payloads != svc._generate_payloads()

    def test_all_six_lab_payloads_survive_the_cap(self):
        """The whole point of the ordering: a 1370-row wordlist must not push
        a lab-solving payload past the per-injection-point budget."""
        if not self._db_available():
            pytest.skip("Payloads.db not built")
        runner = MagicMock()
        runner.run.return_value = ""
        payloads = PathTraversalScanner(runner, MagicMock())._build_payloads()

        for lab, required in self.LAB_PAYLOADS.items():
            assert required in payloads, f"{lab}: {required} fell outside the cap"

    def test_db_payloads_are_deduplicated(self):
        if not self._db_available():
            pytest.skip("Payloads.db not built")
        runner = MagicMock()
        runner.run.return_value = ""
        payloads = PathTraversalScanner(runner, MagicMock())._build_payloads()

        assert len(payloads) == len(set(payloads))

    def test_missing_db_falls_back_to_the_generated_matrix(self):
        """A scan must not die because an optional, gitignored data file has
        not been built."""
        runner = MagicMock()
        runner.run.return_value = ""
        svc = PathTraversalScanner(runner, MagicMock())

        with patch.object(svc, "_load_db_payloads", return_value=[]):
            payloads = svc._build_payloads()

        assert payloads == svc._generate_payloads()
        # Only the depth-scaled entries the fallback generator actually
        # produces; the absolute/prefixed/nullbyte enrichment classes belong
        # to a fuller generator that was not carried over by this merge.
        for required in (
            "../../../etc/passwd",
            "....//....//....//etc/passwd",
            "..%252f..%252f..%252fetc%252fpasswd",
        ):
            assert required in payloads, required

    def test_db_read_failure_is_swallowed(self):
        """`_load_db_payloads` must never raise into the scan loop."""
        runner = MagicMock()
        runner.run.return_value = ""
        svc = PathTraversalScanner(runner, MagicMock())

        with patch.dict("sys.modules", {"Payloads.payload_store": None}):
            assert svc._load_db_payloads() == []

    def test_ordering_interleaves_classes_instead_of_concatenating(self):
        """Flat class-major concatenation put four of the six lab payloads at
        indices 311-725 because `raw` alone holds ~490 wordlist rows. The
        round-robin must surface a distinct class per probe early on."""
        runner = MagicMock()
        runner.run.return_value = ""
        svc = PathTraversalScanner(runner, MagicMock())

        ordered = svc._order_payloads([
            "/etc/passwd", "../etc/passwd", "../../etc/passwd",
            "....//etc/passwd", "..%2fetc%2fpasswd", "..%252fetc%252fpasswd",
        ])

        assert [_classify_payload(p) for p in ordered[:5]] == [
            "absolute", "raw", "collapse", "single", "double"]

    def test_unclassifiable_payloads_are_probed_last(self):
        runner = MagicMock()
        runner.run.return_value = ""
        svc = PathTraversalScanner(runner, MagicMock())

        ordered = svc._order_payloads(["..2fetc2fpasswd", "../etc/passwd"])

        assert ordered[-1] == "..2fetc2fpasswd"

    def test_classifier_assigns_each_lab_payload_to_its_own_class(self):
        expected = {
            "../../../etc/passwd": "raw",
            "/etc/passwd": "absolute",
            "....//....//....//etc/passwd": "collapse",
            "..%252f..%252f..%252fetc%252fpasswd": "double",
            "/var/www/images/../../../etc/passwd": "prefixed",
            "../../../etc/passwd%00.png": "nullbyte",
            "..%2fetc%2fpasswd": "single",
            "..%c0%afetc/passwd": "overlong",
            "..%5cetc\\passwd": "backslash",
        }
        for payload, cls in expected.items():
            assert _classify_payload(payload) == cls, payload

    def test_canonical_chain_outranks_malformed_separator_variants(self):
        """Without this, `..//etc/passwd`-style noise at depth 1-2 buried the
        canonical chain 25 places deep in its own class."""
        assert _payload_is_irregular("../../../etc/passwd") == 0
        assert _payload_is_irregular("..//etc/passwd") == 1

    def test_target_rank_ignores_htpasswd_lookalikes(self):
        """Loose 'passwd' matching let `../.htpasswd` outrank the real target."""
        assert _payload_target_rank("../../../etc/passwd") == 0
        assert _payload_target_rank("../.htpasswd") > 0
