"""Unit tests for app/tools/utils.py.

No test file existed for this module before, despite
normalize_domain_for_memory() fixing a real, documented data-integrity
bug (see that function's own docstring): multiple tool modules
independently stripped the URL scheme but not the port, so the same real
site could be written to the Blackboard under two different domain keys
and fragment the Knowledge Graph. Locking in the exact normalization
behavior here prevents that bug from silently reappearing.
"""
import pytest

from app.tools.utils import clean_ansi_codes, normalize_domain_for_memory

pytestmark = pytest.mark.unit


class TestNormalizeDomainForMemory:
    def test_strips_https_scheme(self):
        """Verify Strips https scheme."""
        assert normalize_domain_for_memory("https://example.com") == "example.com"

    def test_strips_http_scheme(self):
        """Verify Strips http scheme."""
        assert normalize_domain_for_memory("http://example.com") == "example.com"

    def test_strips_path(self):
        """Verify Strips path."""
        assert normalize_domain_for_memory("http://example.com/some/path?x=1") == "example.com"

    def test_strips_port(self):
        """Regression test: this is the actual bug fix - a bare
        `.replace("https://", "").replace("http://", "").split("/")[0]`
        (independently duplicated in several tool modules before this
        function existed) stripped the scheme but left the port attached,
        so "http://example.com:80" normalized to "example.com:80", not
        "example.com" - a different Blackboard key than a scan of the bare
        domain, silently fragmenting one real site into two targets."""
        assert normalize_domain_for_memory("http://example.com:80") == "example.com"
        assert normalize_domain_for_memory("https://example.com:8443/path") == "example.com"

    def test_bare_domain_with_port_unchanged_otherwise(self):
        """Verify Bare domain with port unchanged otherwise."""
        assert normalize_domain_for_memory("example.com:8080") == "example.com"

    def test_bare_domain_no_scheme_no_port(self):
        """Verify Bare domain no scheme no port."""
        assert normalize_domain_for_memory("example.com") == "example.com"

    def test_different_port_qualified_variants_of_the_same_site_collapse_to_one_key(self):
        """The exact scenario this function was written to fix: two
        different port-qualified variants of the same real site must
        normalize to the identical Blackboard key."""
        variant_a = normalize_domain_for_memory("http://example.com:80")
        variant_b = normalize_domain_for_memory("https://example.com:443/dashboard")
        variant_c = normalize_domain_for_memory("example.com")
        assert variant_a == variant_b == variant_c == "example.com"


class TestCleanAnsiCodes:
    def test_strips_color_codes(self):
        """Verify Strips color codes."""
        raw = "\x1b[32mgreen text\x1b[0m"
        assert clean_ansi_codes(raw) == "green text"

    def test_leaves_plain_text_unchanged(self):
        """Verify Leaves plain text unchanged."""
        assert clean_ansi_codes("plain output, nothing fancy") == "plain output, nothing fancy"

    def test_empty_string(self):
        """Verify Empty string."""
        assert clean_ansi_codes("") == ""
