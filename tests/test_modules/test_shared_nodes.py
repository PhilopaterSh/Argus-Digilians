"""Unit tests for app/core/agent/nodes/_shared.py.

This module exists specifically because `_first_web_port`/`_build_target_url`
used to be independently duplicated in nodes/scanner.py and nodes/exploit.py
(specs/checklist.md CHK059/060) - consolidated here as the single source of
truth (Constitution IX). No test locked in the consolidated behavior before
this file, so a future edit to either call site could silently re-diverge
from the other without any test catching it.
"""
import pytest

from app.core.agent.nodes._shared import _build_target_url, _first_web_port

pytestmark = pytest.mark.unit


class TestFirstWebPort:
    def test_prefers_a_common_web_port_even_if_not_first(self):
        """Verify Prefers a common web port even if not first."""
        assert _first_web_port([22, 3306, 443, 8080]) == 443

    def test_prefers_80_over_a_later_common_port(self):
        """Verify Prefers 80 over a later common port."""
        assert _first_web_port([21, 80, 8443]) == 80

    def test_falls_back_to_first_port_when_none_are_common(self):
        """Verify Falls back to first port when none are common."""
        assert _first_web_port([22, 3306, 9999]) == 22

    def test_empty_list_returns_none(self):
        """Verify Empty list returns none."""
        assert _first_web_port([]) is None


class TestBuildTargetUrl:
    def test_bare_domain_gets_http_scheme_for_non_tls_port(self):
        """Verify Bare domain gets http scheme for non tls port."""
        assert _build_target_url("example.com", 8080) == "http://example.com:8080"

    def test_bare_domain_gets_https_scheme_for_443(self):
        """Verify Bare domain gets https scheme for 443."""
        assert _build_target_url("example.com", 443) == "https://example.com:443"

    def test_bare_domain_gets_https_scheme_for_8443(self):
        """Verify Bare domain gets https scheme for 8443."""
        assert _build_target_url("example.com", 8443) == "https://example.com:8443"

    def test_existing_scheme_is_respected_for_host_extraction(self):
        """Verify Existing scheme is respected for host extraction."""
        assert _build_target_url("http://example.com", 8080) == "http://example.com:8080"

    def test_target_with_explicit_port_ignores_the_port_argument(self):
        """A target that already specifies its own port (e.g. discovered via
        a prior tool) must keep that port, not have the `port` argument's
        value silently appended a second time or override it."""
        assert _build_target_url("example.com:9000", 443) == "https://example.com:9000"
