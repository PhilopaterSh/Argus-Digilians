from unittest.mock import MagicMock

import pytest

from app.tools.crawler import (
    PARAM_FINDING_SEP,
    CrawlerService,
    InMemoryBlackboard,
    LocalCurlRunner,
)

pytestmark = pytest.mark.unit


def _runner(*pages):
    """Build a runner whose successive `run()` calls return `pages` in order.

    Args:
        *pages (str): Response bodies, one per fetch, in crawl order. The
            last value is repeated once exhausted so an over-eager crawl
            never raises StopIteration mid-test.

    Returns:
        MagicMock: A runner double accepting `run(cmd, timeout=...)`.
    """
    bodies = list(pages) or [""]

    def _run(cmd, timeout=None):
        """Pop one queued HTML body per fetch so pages differ across requests."""
        return bodies.pop(0) if len(bodies) > 1 else bodies[0]

    runner = MagicMock()
    runner.run.side_effect = _run
    return runner


def _findings(memory, data_type):
    """Extract the raw_data of every persisted finding of `data_type`.

    Args:
        memory (MagicMock): The memory double passed to CrawlerService.
        data_type (str): "link" or "param".

    Returns:
        list[str]: `raw_data` values, in persistence order.
    """
    return [
        call.args[3] for call in memory.add_finding.call_args_list
        if call.args[2] == data_type
    ]


class TestFetchSafety:
    def test_bounds_curl_with_a_timeout(self):
        """Regression: crawl_target had no explicit curl timeout - a live
        check against a real, currently-down practice site during specs/018
        CHK090's own verification showed this would otherwise block on
        command_runner.py's much longer generic default timeout instead of
        failing fast."""
        runner = _runner("")
        svc = CrawlerService(runner, MagicMock())

        svc.crawl_target("http://example.com")

        cmd = runner.run.call_args[0][0]
        assert "--max-time" in cmd
        assert "--connect-timeout" in cmd

    def test_target_url_is_shell_quoted(self):
        """The URL is interpolated into a shell command; it must be quoted."""
        runner = _runner("")
        svc = CrawlerService(runner, MagicMock())

        svc.crawl_target("http://example.com/a'b")

        cmd = runner.run.call_args[0][0]
        assert "'\"'\"'" in cmd, f"URL not shell-quoted: {cmd}"

    def test_fetch_failure_is_swallowed(self):
        """A runner that raises must not abort the crawl."""
        runner = MagicMock()
        runner.run.side_effect = RuntimeError("wsl down")
        svc = CrawlerService(runner, MagicMock())

        report = svc.crawl_target("http://example.com")

        assert "injection points: 0" in report

    def test_empty_response_reports_no_injection_points(self):
        """Verify an unreachable target degrades to an explicit zero."""
        svc = CrawlerService(_runner(""), MagicMock())

        report = svc.crawl_target("http://example.com")

        assert "injection points: 0" in report


class TestAttributeExtraction:
    """Regression: the crawler only extracted double-quoted `href=`/`src=`,
    which structurally misses the endpoints traversal/LFI sinks sit behind.
    PortSwigger's "File path traversal, simple case" exposes its vulnerable
    `/image?filename=` solely in an `<img src>`.
    """

    def test_img_src_endpoint_becomes_a_param_finding(self):
        """An <img src> endpoint yields a parameter finding just like <a href> ones."""
        html = (
            '<html><body>'
            '<img src="/image?filename=23.jpg">'
            '<a href="/product?productId=1">p</a>'
            '</body></html>'
        )
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        params = _findings(memory, "param")
        assert f"http://example.com/image{PARAM_FINDING_SEP}filename" in params
        assert f"http://example.com/product{PARAM_FINDING_SEP}productId" in params

    def test_single_quoted_attributes_are_extracted(self):
        """The old grep required a literal `="` with double quotes."""
        html = "<img src='/image?filename=1.jpg'>"
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert f"http://example.com/image{PARAM_FINDING_SEP}filename" in _findings(
            memory, "param")

    def test_whitespace_around_equals_is_tolerated(self):
        """href = '...' spacing around the equals sign is parsed normally."""
        html = '<a href = "/download?file=x.txt">d</a>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert f"http://example.com/download{PARAM_FINDING_SEP}file" in _findings(
            memory, "param")

    def test_javascript_and_anchor_hrefs_are_skipped(self):
        """javascript: and bare #anchor hrefs are never treated as endpoints."""
        html = '<a href="javascript:void(0)">x</a><a href="#top">y</a>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        report = svc.crawl_target("http://example.com")

        assert "javascript:void(0)" not in report
        assert _findings(memory, "param") == []

    def test_external_hosts_are_dropped(self):
        """Off-host links must not consume the persist budget."""
        html = (
            '<img src="https://cdn.other.net/i?filename=a.jpg">'
            '<img src="/image?filename=1.jpg">'
        )
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        links = _findings(memory, "link")
        assert all("cdn.other.net" not in link for link in links)
        assert any("example.com/image" in link for link in links)


class TestFormExtraction:
    """A GET form's field names are injection points that never appear as
    `?param=` anywhere in the markup."""

    def test_input_names_become_injection_points(self):
        """Form input names (text and select) become /search?doc|lang injection points."""
        html = (
            '<form action="/search" method="GET">'
            '<input type="text" name="doc">'
            '<select name="lang"></select>'
            '</form>'
        )
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        params = _findings(memory, "param")
        assert f"http://example.com/search{PARAM_FINDING_SEP}doc" in params
        assert f"http://example.com/search{PARAM_FINDING_SEP}lang" in params

    def test_actionless_form_falls_back_to_the_page_url(self):
        """A form without action= attaches its inputs to the current page URL."""
        html = '<form><input name="file"></form>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com/browse")

        assert any(
            entry.endswith(f"{PARAM_FINDING_SEP}file")
            for entry in _findings(memory, "param")
        )


class TestSinkCollapse:
    """`sort -u` deduped by string, so twenty product thumbnails differing
    only in filename value consumed the whole persist budget for one sink."""

    def test_duplicate_sinks_collapse_to_one_representative(self):
        """Thirty thumbs sharing /image?filename=N collapse to one representative sink."""
        thumbs = "".join(
            f'<img src="/image?filename={i}.jpg">' for i in range(30)
        )
        memory = MagicMock()
        svc = CrawlerService(_runner(thumbs + '<a href="/p?productId=1">p</a>', ""),
                             memory)

        svc.crawl_target("http://example.com")

        params = _findings(memory, "param")
        image_points = [p for p in params if "/image" in p]
        assert len(image_points) == 1, f"sink not collapsed: {image_points}"
        assert f"http://example.com/p{PARAM_FINDING_SEP}productId" in params

    def test_distinct_param_sets_on_one_path_stay_separate(self):
        """/view?file= and /view?page= stay separate - collapsing by path alone would drop a sink."""
        html = (
            '<a href="/view?file=a">1</a>'
            '<a href="/view?page=2">2</a>'
        )
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        params = _findings(memory, "param")
        assert f"http://example.com/view{PARAM_FINDING_SEP}file" in params
        assert f"http://example.com/view{PARAM_FINDING_SEP}page" in params


class TestRanking:
    def test_file_ish_params_are_persisted_before_bare_links(self):
        """File-bearing parameters are persisted ahead of bare links as higher-value sinks."""
        html = (
            '<a href="/about">a</a>'
            '<a href="/track?ref=hp">r</a>'
            '<img src="/image?filename=1.jpg">'
        )
        memory = MagicMock()
        svc = CrawlerService(_runner(html, "", "", ""), memory)

        svc.crawl_target("http://example.com", store_limit=2)

        links = _findings(memory, "link")
        assert len(links) == 2
        assert "filename" in links[0], f"file-ish param not ranked first: {links}"
        assert "/about" not in links


class TestBreadthFirstCrawl:
    def test_follows_links_one_hop_to_find_a_deeper_sink(self):
        """One BFS hop from a link-only seed page reaches the deeper download sink on /catalog."""
        seed = '<a href="/catalog">catalog</a>'
        catalog = '<img src="/download?file=manual.pdf">'
        memory = MagicMock()
        svc = CrawlerService(_runner(seed, catalog, ""), memory)

        svc.crawl_target("http://example.com", max_depth=2)

        assert f"http://example.com/download{PARAM_FINDING_SEP}file" in _findings(
            memory, "param")

    def test_depth_zero_reproduces_single_page_behaviour(self):
        """max_depth=0 keeps single-page behaviour: only the seed page is fetched."""
        seed = '<a href="/catalog">catalog</a>'
        catalog = '<img src="/download?file=manual.pdf">'
        runner = _runner(seed, catalog, "")
        svc = CrawlerService(runner, MagicMock())

        svc.crawl_target("http://example.com", max_depth=0)

        assert runner.run.call_count == 1

    def test_max_pages_bounds_the_fetch_count(self):
        """max_pages bounds total page fetches no matter how many links the pages carry."""
        many = "".join(f'<a href="/p{i}">p</a>' for i in range(50))
        runner = _runner(many, "", "", "", "", "", "")
        svc = CrawlerService(runner, MagicMock())

        svc.crawl_target("http://example.com", max_pages=3, max_depth=2)

        assert runner.run.call_count <= 3

    def test_parameterized_urls_are_not_refetched_as_pages(self):
        """Following every `?filename=<n>.jpg` variant would burn the page
        budget re-fetching one already-known sink."""
        thumbs = "".join(f'<img src="/image?filename={i}.jpg">' for i in range(10))
        runner = _runner(thumbs, "", "", "")
        svc = CrawlerService(runner, MagicMock())

        svc.crawl_target("http://example.com", max_pages=12, max_depth=2)

        assert runner.run.call_count == 1


class TestLegacyLinkChannel:
    def test_links_are_still_persisted(self):
        """Existing consumers reading data_type='link' must not regress."""
        html = '<img src="/image?filename=1.jpg">'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert "http://example.com/image?filename=1.jpg" in _findings(memory, "link")

    def test_crawl_target_still_returns_a_string(self):
        """WSLBridgeTools exposes this as the Crawl_Target LangChain tool,
        which cannot accept a dict."""
        svc = CrawlerService(_runner('<img src="/image?filename=1.jpg">', ""), MagicMock())

        assert isinstance(svc.crawl_target("http://example.com"), str)


class TestJavaScriptEndpointExtraction:
    """A request target built inside a fetch/axios/XHR call never appears in
    an href/src attribute, so an attribute-only scan cannot see it."""

    def test_fetch_call_endpoint_is_extracted(self):
        """A fetch() call inside a <script> block yields an endpoint/parameter pair."""
        html = '<script>fetch("/api/report?template=summary").then(r => r.json());</script>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert f"http://example.com/api/report{PARAM_FINDING_SEP}template" in _findings(
            memory, "param")

    def test_bare_quoted_path_in_script_is_extracted(self):
        """Catches hand-rolled string concatenation the call patterns miss."""
        html = '<script>var u = "/legacy/view?page=home";</script>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert f"http://example.com/legacy/view{PARAM_FINDING_SEP}page" in _findings(
            memory, "param")

    def test_xhr_open_endpoint_is_extracted(self):
        """An XHR .open('GET', ...) target is harvested as an endpoint with its parameter."""
        html = '<script>x.open("GET", "/data/fetch?doc=a");</script>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert f"http://example.com/data/fetch{PARAM_FINDING_SEP}doc" in _findings(
            memory, "param")

    def test_prose_outside_a_script_block_is_not_treated_as_an_endpoint(self):
        """URL-shaped text in ordinary HTML prose must not become an endpoint."""
        html = '<p>Visit "/not/an?endpoint=1" for details</p>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert _findings(memory, "param") == []

    def test_offhost_js_endpoint_is_dropped(self):
        """Cross-origin JavaScript endpoints are dropped; only same-host ones survive."""
        html = '<script>fetch("https://cdn.other.net/a?file=x");</script>'
        memory = MagicMock()
        svc = CrawlerService(_runner(html, ""), memory)

        svc.crawl_target("http://example.com")

        assert _findings(memory, "param") == []


class TestAttackSurfaceStructure:
    """harvest_attack_surface() is the normalized handoff PathTraversalScanner
    consumes directly - its shape is a contract between the two modules."""

    HTML = (
        '<img src="/image?filename=1.jpg">'
        '<form action="/search" method="GET"><input name="doc"></form>'
        '<script>fetch("/api/x?template=a");</script>'
        '<a href="/my-account">acct</a>'
    )

    def test_surface_exposes_the_documented_keys(self):
        """harvest_attack_surface() exposes exactly the documented surface keys."""
        svc = CrawlerService(_runner(self.HTML, "", ""), MagicMock())

        surface = svc.harvest_attack_surface("http://example.com", max_depth=0)

        for key in ("target", "host", "pages_fetched", "raw_links",
                    "endpoints", "injection_points", "path_segments"):
            assert key in surface, f"missing key: {key}"

    def test_injection_points_are_endpoint_param_pairs(self):
        """injection_points entries are (absolute endpoint, parameter) pairs."""
        svc = CrawlerService(_runner(self.HTML, "", ""), MagicMock())

        surface = svc.harvest_attack_surface("http://example.com", max_depth=0)

        assert ("http://example.com/image", "filename") in surface["injection_points"]
        assert ("http://example.com/search", "doc") in surface["injection_points"]
        assert ("http://example.com/api/x", "template") in surface["injection_points"]

    def test_endpoints_record_their_discovery_source(self):
        """Keyed by full URL, not endpoint: `<form action="/search">` is
        legitimately discovered twice - bare, because `action` is also an
        attribute _ATTR_RE matches, and parameterized from its field names."""
        svc = CrawlerService(_runner(self.HTML, "", ""), MagicMock())

        surface = svc.harvest_attack_surface("http://example.com", max_depth=0)

        sources = {e["url"]: e["source"] for e in surface["endpoints"]}
        assert sources["http://example.com/image?filename=1.jpg"] == "html"
        assert sources["http://example.com/search?doc="] == "form"
        assert sources["http://example.com/api/x?template=a"] == "js"
        assert sources["http://example.com/search"] == "html"

    def test_parameterless_endpoints_become_path_segment_candidates(self):
        """Query-less endpoints land in path_segments as path-traversal candidates."""
        svc = CrawlerService(_runner(self.HTML, "", ""), MagicMock())

        surface = svc.harvest_attack_surface("http://example.com", max_depth=0)

        assert "http://example.com/my-account" in surface["path_segments"]
        # The seed root itself is not a path-segment candidate.
        assert "http://example.com/" not in surface["path_segments"]

    def test_report_names_the_traversal_class_for_the_agent_hint_scanner(self):
        """react_workflow._extract_vulnerability_hints scans this text to
        decide whether to hand the model a Path_Traversal_Scan directive."""
        svc = CrawlerService(_runner(self.HTML, "", ""), MagicMock())

        report = svc.format_surface_report(
            svc.harvest_attack_surface("http://example.com", max_depth=0))

        assert "?filename=" in report
        assert "path-segment injection candidates" in report


class TestStandaloneShims:
    """The __main__ pipeline must run without WSL, paramiko, or the SQLite
    blackboard - the shims satisfy the same duck-typed contracts."""

    def test_local_runner_returns_stdout(self):
        """LocalCurlRunner returns the command's stdout."""
        assert LocalCurlRunner().run("echo hello").strip() == "hello"

    def test_local_runner_swallows_failure(self):
        """A non-zero exit yields empty output instead of raising."""
        assert LocalCurlRunner().run("exit 7") == ""

    def test_local_runner_accepts_commandrunner_kwargs(self):
        """CommandRunner-style kwargs (timeout, show_prompt) are accepted harmlessly."""
        assert LocalCurlRunner().run("echo x", timeout=5, show_prompt=True).strip() == "x"

    def test_in_memory_blackboard_roundtrips_findings(self):
        """InMemoryBlackboard persists findings per host and filters them on read."""
        mem = InMemoryBlackboard()
        mem.add_finding("example.com", "crawler", "param", "a\tb", "s")
        mem.add_finding("other.com", "crawler", "param", "c\td", "s")

        rows = mem.get_detailed_findings("example.com")

        assert len(rows) == 1
        assert rows[0]["raw_data"] == "a\tb"

    def test_crawler_runs_against_the_in_memory_shims(self):
        """Full substitution check: no MagicMock anywhere in the data path."""
        mem = InMemoryBlackboard()
        svc = CrawlerService(_runner('<img src="/image?filename=1.jpg">', ""), mem)

        surface = svc.harvest_attack_surface("http://example.com", max_depth=0)

        assert surface["injection_points"] == [("http://example.com/image", "filename")]
        assert any(f["data_type"] == "param" for f in
                   mem.get_detailed_findings("example.com"))
