"""Unit tests for app/tools/wsl_bridge.py::WSLBridge.ensure_ssh_service.

No test file existed for this module before, despite it being the
readiness check command_runner.py's SSH fallback path depends on directly.
`start_cmd`'s `distro` value comes from WSLConfig (an operator-set env var
at startup, not per-request untrusted input), so the shell=True usage here
is not the same class of concern as the self_heal.py command-injection fix
covered elsewhere - these tests lock in the actual control-flow behavior
(skip vs. start), not a security property.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.tools.wsl_bridge import WSLBridge, WSLConfig

pytestmark = pytest.mark.unit


def _make_bridge(distro="kali-linux"):
    """Build a WSLBridge with a fixed WSLConfig for deterministic assertions.

    Args:
        distro (str): The distro name to set on the config.

    Returns:
        WSLBridge: Configured with the given distro.
    """
    return WSLBridge(WSLConfig(distro=distro))


class TestEnsureSshService:
    def test_returns_true_without_starting_anything_when_port_already_open(self):
        """If the SSH port already accepts connections, ensure_ssh_service()
        must return True immediately without spawning a WSL subprocess."""
        bridge = _make_bridge()
        with patch("app.tools.wsl_bridge.socket.socket") as mock_socket_cls, \
             patch("app.tools.wsl_bridge.subprocess.run") as mock_run:
            mock_socket_cls.return_value.__enter__.return_value.connect_ex.return_value = 0

            result = bridge.ensure_ssh_service()

            assert result is True
            mock_run.assert_not_called()

    def test_starts_sshd_via_wsl_when_port_is_closed(self):
        """When the port is closed, must invoke `wsl -d <distro> -u root
        bash -c "mkdir -p /run/sshd && /usr/sbin/sshd"` for the configured distro."""
        bridge = _make_bridge(distro="kali-linux")
        with patch("app.tools.wsl_bridge.socket.socket") as mock_socket_cls, \
             patch("app.tools.wsl_bridge.subprocess.run") as mock_run, \
             patch("app.tools.wsl_bridge.time.sleep"):
            mock_socket_cls.return_value.__enter__.return_value.connect_ex.return_value = 1
            mock_run.return_value = MagicMock(returncode=0)

            result = bridge.ensure_ssh_service()

            assert result is True
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            start_cmd = args[0]
            assert "wsl -d kali-linux -u root bash -c" in start_cmd
            assert "/usr/sbin/sshd" in start_cmd
            assert kwargs.get("timeout") == 10

    def test_returns_false_on_any_exception(self):
        """A socket or subprocess failure must be swallowed and reported as
        False, never raised - callers treat this as a best-effort readiness probe."""
        bridge = _make_bridge()
        with patch("app.tools.wsl_bridge.socket.socket", side_effect=OSError("boom")):
            assert bridge.ensure_ssh_service() is False
