"""Unit tests for app/tools/recon.py::ReconService._nmap_needs_fallback.

No test file existed for this module before, despite this method encoding
a real, previously-tuned WAF/CDN-detection heuristic (per its own
docstring: "both failure modes seen behind a WAF/CDN"). Only the static,
pure-logic method is covered here - the rest of ReconService (subprocess/
WSL-backed methods) would need heavier mocking, out of scope for this pass.
"""
import pytest

from app.tools.recon import ReconService

pytestmark = pytest.mark.unit


class TestNmapNeedsFallback:
    def test_empty_output_needs_fallback(self):
        """Verify Empty output needs fallback."""
        assert ReconService._nmap_needs_fallback("") is True

    def test_command_runner_error_needs_fallback(self):
        """A command_runner-level error/timeout string (not real nmap
        output at all) must trigger the fallback, not be mistaken for a
        clean "no ports open" scan."""
        assert ReconService._nmap_needs_fallback("Error: Command timed out after 180s.") is True
        assert ReconService._nmap_needs_fallback("Error (Code 1): connection refused") is True

    def test_host_seems_down_needs_fallback(self):
        """The WAF/CDN case this method was written for: nmap's default
        ICMP/TCP host-discovery ping gets dropped, reporting the host down
        even though it's actually serving traffic - -Pn skips this."""
        nmap_output = (
            "Starting Nmap 7.94\n"
            "Note: Host seems down. If it is really up, but blocking our ping probes, try -Pn\n"
            "Nmap done: 1 IP address (0 hosts up) scanned in 3.02 seconds"
        )
        assert ReconService._nmap_needs_fallback(nmap_output) is True

    def test_real_port_list_does_not_need_fallback(self):
        """Verify Real port list does not need fallback."""
        nmap_output = (
            "PORT     STATE SERVICE VERSION\n"
            "80/tcp   open  http    nginx 1.24\n"
            "443/tcp  open  https   nginx 1.24"
        )
        assert ReconService._nmap_needs_fallback(nmap_output) is False

    def test_output_with_no_tcp_port_line_needs_fallback(self):
        """Nmap can complete "cleanly" (no error, no explicit "host down")
        and still produce no usable port list - the final catch-all check."""
        nmap_output = "Starting Nmap 7.94\nNmap done: 1 IP address (1 host up) scanned in 1.02 seconds"
        assert ReconService._nmap_needs_fallback(nmap_output) is True
