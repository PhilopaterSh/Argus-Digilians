"""Facade-level safety wiring tests (ARG-01/03/04 remediation, 2026-10-30).

The SafetyLayer sat dormant in app/core/safety.py until it was wired into
WSLBridgeTools: every target-taking facade method now runs
``validate_target`` first, and ``Run_Kali_Command`` runs ``guard_command``
before touching the bridge. These tests prove that wiring end-to-end
without a live Kali bridge (the guard and target checks return before any
command execution).
"""
from app.core.safety import SafetyLayer
from app.tools.tool_registry import WSLBridgeTools


def test_facade_rejects_private_target():
    """Verify a private-range target is refused before any tool runs."""
    bridge = WSLBridgeTools()
    out = bridge.run_nikto("http://192.168.1.1")
    assert out.startswith("[SAFETY] Target rejected:")
    assert "private range" in out.lower()


def test_facade_rejects_non_fqdn_target():
    """Verify shell-metacharacter targets fail the FQDN allowlist."""
    bridge = WSLBridgeTools()
    out = bridge.crawl_target("example.com; rm -rf /")
    assert out.startswith("[SAFETY] Target rejected:")
    assert "fqdn" in out.lower()


def test_facade_allows_public_target_and_delegates():
    """Verify a clean public target clears validation and reaches the service.

    The runner is replaced with a stub so no live Kali bridge is needed; the
    assertion is that the safety seam let the call through.
    """
    bridge = WSLBridgeTools()
    calls = []

    def fake_run(command, show_prompt=False, timeout=None):
        calls.append(command)
        return "ok"

    bridge.runner.run = fake_run
    out = bridge.run_nikto("https://example.com")
    assert out != "" and not out.startswith("[SAFETY]")
    assert calls, "expected the delegate to reach the command runner"


def test_facade_run_kali_command_blocks_destructive():
    """Verify Run_Kali_Command refuses destructive commands via guard_command."""
    bridge = WSLBridgeTools()
    out = bridge.run_kali_command("rm -rf /tmp/target")
    assert out.startswith("BLOCKED:")


def test_safety_layer_instance_shared():
    """Verify the facade owns one SafetyLayer for audit-log continuity."""
    bridge = WSLBridgeTools()
    assert isinstance(bridge.safety, SafetyLayer)
