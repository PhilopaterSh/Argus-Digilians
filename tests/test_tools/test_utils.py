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

from app.tools.utils import (
    clean_ansi_codes,
    find_sensitive_content_match,
    normalize_domain_for_memory,
)

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


class TestFindSensitiveContentMatch:
    def test_matches_exact_substring_indicator(self):
        """The common case: /etc/passwd's password field is the literal
        "x" default, so the exact-substring SENSITIVE_CONTENT_INDICATORS
        entry matches directly - no regex fallback needed."""
        body = "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin"
        summary = find_sensitive_content_match(body)
        assert summary == "LFI/Path Traversal Confirmed (/etc/passwd read success)"

    def test_matches_other_exact_indicators(self):
        """Verify the other three SENSITIVE_CONTENT_INDICATORS entries
        (unaffected by this change) still match via find_sensitive_content_match."""
        assert find_sensitive_content_match("DB_PASSWORD=hunter2") == (
            "Secret Disclosure Confirmed (Database configuration leaked)"
        )
        assert find_sensitive_content_match("<appSettings>...</appSettings>") == (
            "Web Configuration Leak Confirmed (web.config read success)"
        )
        assert find_sensitive_content_match("uid=0(root) gid=0(root)") == (
            "RCE Confirmed (id command executed successfully)"
        )

    def test_regex_fallback_catches_non_x_password_field(self):
        """Live-discovered 2026-08-02: a real /etc/passwd read against a
        target whose root entry uses "*" (no direct login) instead of the
        literal "x" in the password field was genuinely successful evidence
        but never matched the exact-substring "root:x:0:0:" indicator - a
        false negative. The regex fallback must still catch it."""
        body = "root:*:0:0:root:/root:/bin/bash\n"
        summary = find_sensitive_content_match(body)
        assert summary == "LFI/Path Traversal Confirmed (/etc/passwd read success)"

    def test_regex_fallback_catches_empty_password_field(self):
        """Another real variant: an empty password field (::0:0:)."""
        body = "root::0:0:root:/root:/bin/bash\n"
        assert find_sensitive_content_match(body) is not None

    def test_does_not_match_unrelated_uid_gid_pair(self):
        """The regex must stay scoped to root's specific UID:GID (0:0) -
        an unrelated non-root passwd line (e.g. a regular user account)
        must not false-positive just because it also has a colon-separated
        shape."""
        body = "alice:x:1001:1001:Alice:/home/alice:/bin/bash\n"
        assert find_sensitive_content_match(body) is None

    def test_returns_none_for_clean_response(self):
        """A genuinely clean response (no signature, no /etc/passwd-shaped
        content at all) must not match anything."""
        assert find_sensitive_content_match("<html>404 Not Found</html>") is None

    def test_returns_none_for_empty_or_none_text(self):
        """Verify Returns none for empty or none text."""
        assert find_sensitive_content_match("") is None
        assert find_sensitive_content_match(None) is None
