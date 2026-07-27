import subprocess
from unittest.mock import MagicMock, patch

from app.tools.path_traversal import PathTraversalScanner


def _make_runner(response_map: dict, default: str = "<html>Not Found</html>"):
    """Mock CommandRunner whose `.run()` reply depends on which substring
    appears in the command, so tests don't couple to payload/param iteration
    order. `shuf` (PayloadsAllTheThings sampling) returns empty by default so
    the payload set is deterministic unless a test overrides it.

    Args:
        response_map (dict): Maps a command substring to the canned
            response `.run()` should return when that substring appears
            in the command. A `"http_code"` key overrides the wake-probe
            (`_wait_until_awake`) status-only curl reply.
        default (str): Reply returned when no `response_map` substring
            matches the command.

    Returns:
        MagicMock: A mock CommandRunner with `.run` wired to the behavior
        above.
    """
    def run(command, timeout=None):
        """Return the canned reply for `command` per `response_map`/`default`.

        Args:
            command (str): The shell command the scanner issued.
            timeout: Accepted for signature compatibility with the real
                CommandRunner.run(); unused by this fake.

        Returns:
            str: The matching canned response, `""` for a `shuf` sampling
            call, or `default` otherwise.
        """
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
    """Build a mock ArgusMemory whose crawler-discovered links are `links`.

    Args:
        links (list[str] | None): Crawler-discovered link URLs to expose
            via `get_detailed_findings()`; defaults to none.

    Returns:
        MagicMock: A mock memory service with `get_detailed_findings()`
        returning one `"link"`-typed finding per entry in `links`.
    """
    memory = MagicMock()
    memory.get_detailed_findings.return_value = [
        {"data_type": "link", "raw_data": link} for link in (links or [])
    ]
    return memory


class TestPathTraversalScan:
    @patch("app.tools.path_traversal.time.sleep")
    def test_confirms_etc_passwd_read_via_content_signature(self, _sleep):
        """A body containing the /etc/passwd signature is a confirmed finding,
        recorded in memory with the dedicated 'path_traversal' tool name.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
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
        """Verify Reports clean when no signature found.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({}, default="<html>Nothing here</html>")
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com")

        assert "No path-traversal vulnerabilities confirmed" in report
        memory.add_finding.assert_not_called()

    @patch("app.tools.path_traversal.time.sleep")
    def test_default_max_probes_reaches_depth_six_for_first_injection_point(self, _sleep):
        """Regression test: the previous max_probes=40 default stopped the
        depth-by-depth sweep right after depth 4 (10 payloads/depth x 4 =
        40), so depth 5-6's classic deep traversal payloads - needed for
        any webroot nested 5+ directories deep - were never sent, even for
        the very first injection point. The default must cover a full
        6-depth sweep for at least one injection point.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({"../../../../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash"})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com", params=["file"])

        assert "Path Traversal Success" in report

    @patch("app.tools.path_traversal.time.sleep")
    def test_emits_multiple_encoding_variants(self, _sleep):
        """The encoding matrix must produce raw, single, and double URL-encoded
        forms of the same traversal, not just one representation.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
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
        ahead of the static fallback list.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({})
        memory = _memory_with_links(["http://example.com/view?report=1&x=2"])
        svc = PathTraversalScanner(runner, memory)

        svc.run_traversal_scan("http://example.com", max_probes=500)

        commands = "\n".join(c.args[0] for c in runner.run.call_args_list)
        assert "report=" in commands  # crawler-derived param used
        assert "x=" in commands

    @patch("app.tools.path_traversal.time.sleep")
    def test_windows_win_ini_signature_confirmed(self, _sleep):
        """Verify Windows win.ini signature confirmed.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
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
        probes it - reproducing the PortSwigger file-path-traversal lab.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
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
        must never be probed with traversal payloads.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
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
        """Verify Respects max probes ceiling.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
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


class TestProbeBudgetCoverage:
    @patch("app.tools.path_traversal.time.sleep")
    def test_every_discovered_injection_point_is_probed_by_default(self, _sleep):
        """Regression: `max_probes` was a *global* 120-probe pool, so with 60
        payloads only the first two of the twelve static candidates were ever
        tried - a vulnerable `filename` (9th in probe order) or `lang` (12th)
        returned a false 'no vulnerability confirmed'. The budget is now per
        injection point, so every discovered parameter must receive probes.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        points = svc._discover_injection_points("http://example.com", None)
        svc.run_traversal_scan("http://example.com")

        commands = "\n".join(c.args[0] for c in runner.run.call_args_list)
        unprobed = [param for _, param in points if f"{param}=" not in commands]
        assert not unprobed, f"injection points never probed: {unprobed}"

    @patch("app.tools.path_traversal.time.sleep")
    def test_vulnerable_last_ranked_param_is_still_confirmed(self, _sleep):
        """A sink on the lowest-priority discovered parameter must still be
        found under the default budget.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({"lang=../../../etc/passwd": "root:x:0:0:root:/root:/bin/bash"})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com")

        assert "Path Traversal Success" in report
        assert "param=lang" in report

    @patch("app.tools.path_traversal.time.sleep")
    def test_observed_params_outrank_blind_guesses_in_budget(self, _sleep):
        """An observed (tier-0) param earns the full encoding matrix; a blind
        static guess gets only the high-yield prefix. Without this split, a
        bare host cost 12 x 60 probes - roughly six minutes against a remote
        target - to brute-force parameter names the app never even reads.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({
            "http://example.com/'": '<html><img src="/image?filename=1.jpg"></html>',
        })
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        svc.run_traversal_scan("http://example.com")

        commands = [c.args[0] for c in runner.run.call_args_list]
        observed = [c for c in commands if "filename=" in c and "/image?" in c]
        guess = [c for c in commands if "lang=" in c]
        assert len(observed) == 60, f"observed param should get the full matrix, got {len(observed)}"
        assert len(guess) == 12, f"blind guess should get the truncated set, got {len(guess)}"

    def test_payload_order_is_encoding_class_major(self):
        """Truncating a budget must keep plain `../` chains at every depth
        rather than spending it all on depth-1's exotic encodings.
        """
        runner = _make_runner({})
        svc = PathTraversalScanner(runner, MagicMock())

        payloads = svc._build_payloads()

        # The high-yield prefix is raw traversal for both OS families, all depths.
        assert all("%" not in p for p in payloads[:12]), payloads[:12]
        assert "../../../../../../etc/passwd" in payloads[:12]
        # Encoded forms come afterwards, not interleaved into the prefix.
        assert any("%2f" in p for p in payloads[12:])

    @patch("app.tools.path_traversal.time.sleep")
    def test_confirmed_point_stops_consuming_its_budget(self, _sleep):
        """Once a parameter is proven vulnerable, the remaining encodings only
        re-prove the same sink - the scan should move on rather than burn the
        rest of that point's budget.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({"file=../etc/passwd": "root:x:0:0:root:/root:/bin/bash"})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("http://example.com", params=["file"])

        assert "Path Traversal Success" in report
        probes = [c for c in runner.run.call_args_list if "file=" in c.args[0]]
        assert len(probes) < 60, "scan kept probing a parameter already confirmed vulnerable"

    @patch("app.tools.path_traversal.time.sleep")
    def test_global_ceiling_still_bounds_total_probes(self, _sleep):
        """`max_total_probes` must cap the scan even when many injection
        points each carry a full per-point budget.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        svc.run_traversal_scan("http://example.com", max_total_probes=75)

        probes = [c for c in runner.run.call_args_list if "?" in c.args[0] and "=" in c.args[0]]
        # Wake/discovery curls carry no injected param; count only real probes.
        payload_probes = [c for c in probes if "etc" in c.args[0] or "win.ini" in c.args[0]]
        assert len(payload_probes) <= 75


class TestDeterminism:
    """Regression: the same scan against the same vulnerable target could
    report FOUND on one run and a confident "no vulnerabilities confirmed" on
    the next. Endpoint discovery hangs off a single root-page fetch, and one
    transient stall silently dropped every observed injection point, leaving
    the scan blind-guessing while the report looked identically confident.
    """

    PAGE = '<html><body><img src="/image?filename=23.jpg"></body></html>'

    def _flaky_runner(self, fail_first_n_page_fetches):
        """Mock runner whose root-page content fetch fails `n` times first.

        Args:
            fail_first_n_page_fetches (int): How many root-page content
                fetches return empty before one succeeds.

        Returns:
            MagicMock: A mock CommandRunner with `.run` wired accordingly.
        """
        state = {"page_fetches": 0}

        def run(command, timeout=None):
            """Return a canned reply, stalling the first N page fetches.

            Args:
                command (str): The shell command the scanner issued.
                timeout: Accepted for signature compatibility; unused.

            Returns:
                str: The canned response for this command.
            """
            if "-o /dev/null" in command and "http_code" in command:
                return "200"
            if command.startswith("shuf"):
                return ""
            # Root-page content fetch (no injected param in the URL).
            if "?" not in command.split("connect-timeout 5 ", 1)[-1]:
                state["page_fetches"] += 1
                if state["page_fetches"] <= fail_first_n_page_fetches:
                    return ""
                return self.PAGE
            if "/image?filename=../etc/passwd" in command:
                return "root:x:0:0:root:/root:/bin/bash"
            return "<html>Not Found</html>"

        mock = MagicMock()
        mock.run.side_effect = run
        return mock

    @patch("app.tools.path_traversal.time.sleep")
    def test_transient_page_fetch_failure_is_retried_not_fatal(self, _sleep):
        """One stalled root-page fetch must not cost the whole tier-0 surface.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        svc = PathTraversalScanner(self._flaky_runner(1), _memory_with_links())

        report = svc.run_traversal_scan("http://example.com")

        assert "Path Traversal Success" in report
        assert "endpoint=http://example.com/image" in report

    @patch("app.tools.path_traversal.time.sleep")
    def test_scan_is_stable_across_repeated_runs(self, _sleep):
        """Same target, same vulnerability, repeated runs - the verdict must
        not flip.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        verdicts = set()
        for _ in range(5):
            svc = PathTraversalScanner(self._flaky_runner(1), _memory_with_links())
            verdicts.add("Path Traversal Success" in svc.run_traversal_scan("http://example.com"))
        assert verdicts == {True}, "scan verdict is non-deterministic across runs"

    @patch("app.tools.path_traversal.time.sleep")
    def test_blind_only_scan_is_reported_as_low_confidence(self, _sleep):
        """When discovery yields no observed params, a clean result must say so
        rather than masquerading as a thorough all-clear.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        # Every page fetch fails -> nothing observed, only static guesses.
        svc = PathTraversalScanner(self._flaky_runner(99), _memory_with_links())

        report = svc.run_traversal_scan("http://example.com")

        assert "No path-traversal vulnerabilities confirmed" in report
        assert "LOW CONFIDENCE" in report
        assert "observed: 0" in report

    @patch("app.tools.path_traversal.time.sleep")
    def test_report_distinguishes_observed_from_guessed_points(self, _sleep):
        """The meta line must expose the attack surface actually covered, so
        two runs that disagree can be told apart at a glance.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        svc = PathTraversalScanner(self._flaky_runner(0), _memory_with_links())

        report = svc.run_traversal_scan("http://example.com")

        assert "observed: 1" in report
        assert "guessed: 12" in report

    @patch("app.tools.path_traversal.time.sleep")
    def test_mirror_enrichment_payloads_are_actually_probed(self, _sleep):
        """Regression: a hardcoded per-point budget of 60 truncated exactly the
        mirror-sampled payloads, which `_build_payloads` appends at index 60+,
        so PayloadsAllTheThings enrichment never fired.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({"shuf": "MIRROR_ONLY_PAYLOAD\n"})
        svc = PathTraversalScanner(runner, _memory_with_links())

        svc.run_traversal_scan("http://example.com", params=["file"])

        commands = "\n".join(c.args[0] for c in runner.run.call_args_list)
        assert "MIRROR_ONLY_PAYLOAD" in commands

    @patch("app.tools.path_traversal.time.sleep")
    def test_empty_responses_are_surfaced_not_swallowed(self, _sleep):
        """A probe that times out proves nothing; a clean verdict built on
        silent timeouts must admit it.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({}, default="")
        svc = PathTraversalScanner(runner, _memory_with_links())

        report = svc.run_traversal_scan("http://example.com")

        assert "empty responses:" in report
        assert "not a clean bill of health" in report


class TestUnreachableTarget:
    @patch("app.tools.path_traversal.time.sleep")
    def test_dead_target_reports_unreachable_not_no_vuln(self, _sleep):
        """A target that only returns 504/000 must be reported as UNREACHABLE,
        distinct from a clean 'no vulnerability' result - and must not record
        any finding.

        Args:
            _sleep: Patched no-op for time.sleep so the test runs instantly.
        """
        runner = _make_runner({"http_code": "504"})
        memory = _memory_with_links()
        svc = PathTraversalScanner(runner, memory)

        report = svc.run_traversal_scan("https://dead.example.com")

        assert "TARGET UNREACHABLE" in report
        assert "No path-traversal vulnerabilities confirmed" not in report
        memory.add_finding.assert_not_called()
