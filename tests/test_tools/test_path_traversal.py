import subprocess
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

        # Derived, not hardcoded: the matrix grew from 60 to 94 payloads when
        # the absolute/prefixed/nullbyte filter-bypass classes were added, and
        # a literal here would have to be chased every time it changes. What
        # matters is the *split*, not the absolute size.
        expected_full = len(
            PathTraversalScanner(_make_runner({}), MagicMock())._build_payloads()
        )
        svc.run_traversal_scan("http://example.com")

        commands = [c.args[0] for c in runner.run.call_args_list]
        observed = [c for c in commands if "filename=" in c and "/image?" in c]
        guess = [c for c in commands if "lang=" in c]
        assert len(observed) == expected_full, (
            f"observed param should get the full matrix, got {len(observed)}")
        assert len(guess) == 27, (
            f"blind guess should get the truncated set, got {len(guess)}")
        assert len(guess) < len(observed)

    def test_payload_order_is_encoding_class_major(self):
        """Truncating a budget must keep the high-yield payloads rather than
        spending it all on depth-1's exotic encodings.

        The high-yield prefix is the `absolute` class (4 payloads - the only
        thing that beats a filter rejecting traversal sequences outright) then
        the plain `../` chains for both OS families at every depth (12), which
        is exactly the 16-probe `max_guess_probes` default.
        """
        runner = _make_runner({})
        svc = PathTraversalScanner(runner, MagicMock())

        # The generator's ordering, not the DB's: `_load_db_payloads()`
        # round-robins across classes instead of concatenating them, because a
        # 1370-row wordlist puts ~490 entries in `raw` alone.
        payloads = svc._generate_payloads()
        prefix = payloads[:16]

        assert "/etc/passwd" in prefix, prefix                     # absolute
        assert "../../../../../../etc/passwd" in prefix, prefix    # raw, deepest
        # Exotic encodings must not be interleaved into the prefix...
        assert all("%c0%af" not in p and "%5c" not in p and "%252f" not in p
                   for p in prefix), prefix
        # ...but must still be present later in the list.
        assert any("%c0%af" in p for p in payloads[16:])
        assert any("%252f" in p for p in payloads[16:])

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

        assert "MIRROR_ONLY_PAYLOAD" in svc._generate_payloads()

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


class TestFilterBypassPayloadClasses:
    """Live failure 2026-07-27: a PortSwigger lab whose `filename` parameter
    was correctly discovered and swept with every payload of the time returned
    no finding. `_build_payloads()` iterates `range(1, MAX_DEPTH + 1)`, so
    EVERY payload it could emit began with at least one `../` - and the only
    working value was a bare `/etc/passwd`, a string the generator could not
    produce at any MAX_DEPTH setting.

    These tests pin the three classes added to close that hole. Each asserts
    the exact string the corresponding PortSwigger lab requires, so a future
    refactor of the encoding matrix cannot silently drop one.
    """

    @staticmethod
    def _payloads():
        """Build the payload matrix with mirror sampling disabled.

        Returns:
            list[str]: The deterministic, generated-only payload set.
        """
        runner = MagicMock()
        runner.run.return_value = ""          # `shuf` -> no mirror enrichment
        return PathTraversalScanner(runner, MagicMock())._generate_payloads()

    def test_absolute_class_solves_absolute_path_bypass(self):
        """Lab: traversal sequences blocked with absolute path bypass."""
        assert "/etc/passwd" in self._payloads()

    def test_absolute_class_covers_windows_and_encoding(self):
        payloads = self._payloads()
        assert "/windows/win.ini" in payloads
        assert "%2fetc%2fpasswd" in payloads

    def test_prefixed_class_solves_validation_of_start_of_path(self):
        """Lab: file path traversal, validation of start of path."""
        assert "/var/www/images/../../../etc/passwd" in self._payloads()

    def test_nullbyte_class_solves_extension_validation(self):
        """Lab: validation of file extension with null byte bypass."""
        assert "../../../etc/passwd%00.png" in self._payloads()

    def test_previously_covered_lab_payloads_are_not_regressed(self):
        """The three original lab solutions must survive the reordering."""
        payloads = self._payloads()
        for required in (
            "../../../etc/passwd",                       # simple case
            "....//....//....//etc/passwd",              # stripped non-recursively
            "..%252f..%252f..%252fetc%252fpasswd",       # superfluous URL-decode
        ):
            assert required in payloads, required

    def test_absolute_class_is_probed_first(self):
        """It is the cheapest class (4 payloads) and the only one that beats a
        filter rejecting traversal sequences outright, so a truncated budget
        must reach it."""
        assert self._payloads()[0] == "/etc/passwd"

    def test_matrix_is_deduplicated(self):
        payloads = self._payloads()
        assert len(payloads) == len(set(payloads))

    def test_every_encoding_class_contributes_payloads(self):
        """A class named in _ENCODING_CLASS_ORDER but never populated would be
        a silent typo - the emit loop skips missing keys without error."""
        from app.tools.path_traversal import _ENCODING_CLASS_ORDER

        payloads = self._payloads()
        markers = {
            "absolute": "/etc/passwd",
            "raw": "../etc/passwd",
            "collapse": "....//etc/passwd",
            "single": "..%2fetc%2fpasswd",
            "double": "..%252fetc%252fpasswd",
            "nullbyte": "../etc/passwd%00.png",
            "prefixed": "/var/www/images/../etc/passwd",
            "overlong": "..%c0%afetc/passwd",
            "backslash": "..%5cwindows\\win.ini",
        }
        assert set(markers) == set(_ENCODING_CLASS_ORDER), "class list drifted"
        for cls, marker in markers.items():
            assert marker in payloads, f"class {cls} produced nothing ({marker})"

    def test_guess_budget_default_reaches_the_canonical_payload(self):
        """Regression: the DB path round-robins across the nine classes, which
        moved `../../../etc/passwd` from index 8 to index 19. At the previous
        16-probe guess budget a genuinely vulnerable blind-guess parameter went
        unconfirmed. The default must cover the canonical depth-3 chain."""
        import inspect

        signature = inspect.signature(PathTraversalScanner.run_traversal_scan)
        default = signature.parameters["max_guess_probes"].default
        assert default == 27

        runner = MagicMock()
        runner.run.return_value = ""
        payloads = PathTraversalScanner(runner, MagicMock())._build_payloads()
        for required in ("../../../etc/passwd", "/etc/passwd"):
            assert required in payloads[:default], (
                f"{required} sits past the blind-guess budget of {default}")

    def test_tool_registry_guess_budget_default_stays_in_sync(self):
        """WSLBridgeTools.run_traversal_scan re-declares max_guess_probes, so
        a stale value there silently overrides the scanner's own default on
        every agent-initiated scan.

        Read from source rather than imported: app.tools.tool_registry pulls in
        command_runner -> paramiko, which is not a test dependency.
        """
        import pathlib
        import re

        source = (pathlib.Path(__file__).resolve().parents[2]
                  / "app" / "tools" / "tool_registry.py").read_text(encoding="utf-8")
        match = re.search(
            r"def run_traversal_scan\([^)]*max_guess_probes=(\d+)", source, re.S)
        assert match, "run_traversal_scan signature not found in tool_registry.py"
        assert int(match.group(1)) == 27, (
            f"tool_registry default is {match.group(1)}, scanner default is 27")


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
        for required in self.LAB_PAYLOADS.values():
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
