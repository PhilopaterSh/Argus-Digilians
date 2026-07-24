"""Unit tests for app/tools/command_runner.py::CommandRunner.

No test file existed for this module before - it executes real commands
via WSL/SSH and has already had one real bug found and fixed here
(2026-07-19: `_run_ssh` carried an unmodified `bash -lc` login-shell
invocation from an earlier merge, which sources shell profile files and
can corrupt tool-output parsers with banner/MOTD text; reverted to a
profile-free invocation, made unnecessary by `_with_safe_path()`'s own
explicit PATH export). These tests lock in that fix and the WAF-detection
behavior, rather than leaving this security-relevant class with zero
regression coverage.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.tools.command_runner import CommandRunner

pytestmark = pytest.mark.unit


def _make_runner(host="127.0.0.1", distro="kali-linux", user="kali"):
    """Build a CommandRunner with a fake bridge exposing the given WSLConfig-shaped fields.

    Args:
        host (str): `bridge.config.host` value - "127.0.0.1"/"localhost"
            routes `run()` to `_run_direct_wsl`, anything else to `_run_ssh`.
        distro (str): `bridge.config.distro` value.
        user (str): `bridge.config.user` value.

    Returns:
        CommandRunner: Wired to the fake bridge.
    """
    bridge = MagicMock()
    bridge.config.host = host
    bridge.config.distro = distro
    bridge.config.user = user
    return CommandRunner(bridge)


class TestRunDirectWsl:
    def test_invokes_wsl_with_bash_dash_c_not_dash_lc(self):
        """Regression test (2026-07-19): a login-shell `bash -lc` invocation
        was carried unmodified through an earlier merge - `-lc` sources
        shell profile files (/etc/profile etc.), which can print banner/MOTD
        text that corrupts tool-output parsers (nmap XML, gobuster, ...).
        Must invoke plain `bash -c` - `_with_safe_path()` already handles
        PATH explicitly, so profile sourcing was never actually needed.
        """
        runner = _make_runner()
        with patch("app.tools.command_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            runner.run("echo hi")

            args, _ = mock_run.call_args
            wsl_cmd = args[0]
            assert wsl_cmd[:2] == ["wsl", "-d"]
            assert "kali-linux" in wsl_cmd
            bash_idx = wsl_cmd.index("bash")
            assert wsl_cmd[bash_idx + 1] == "-c", (
                "must be a plain 'bash -c', not a login-shell 'bash -lc'"
            )

    def test_prepends_safe_path_export_to_the_command(self):
        """The actual command passed to bash -c must be prefixed with
        _with_safe_path()'s PATH export, not the raw command alone."""
        runner = _make_runner()
        with patch("app.tools.command_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            runner.run("echo hi")

            args, _ = mock_run.call_args
            wsl_cmd = args[0]
            full_command = wsl_cmd[-1]
            assert full_command.startswith('export PATH="$PATH:')
            assert full_command.endswith("echo hi")

    def test_waf_block_detected_returns_stop_message_not_raw_output(self):
        """A WAF/block-page indicator in the output must short-circuit to
        the explicit [STOP] alert, not the raw (possibly misleading) body."""
        runner = _make_runner()
        with patch("app.tools.command_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Cloudflare ray ID: abc123 - Access Temporarily Restricted", stderr=""
            )
            result = runner.run("curl http://example.com")

        assert result.startswith("[STOP] [WAF ALERT]")

    def test_command_not_found_gives_install_suggestion(self):
        """A real 'command not found' failure should suggest the self-heal path, not a bare error dump."""
        runner = _make_runner()
        with patch("app.tools.command_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=127, stdout="", stderr="nmap: command not found")
            result = runner.run("nmap -sV target.com")

        assert "not installed in WSL" in result
        assert "sudo apt install -y nmap" in result


class TestWithSafePath:
    def test_prefixes_common_tool_install_locations(self):
        """Verify Prefixes common tool install locations."""
        result = CommandRunner._with_safe_path("whoami")
        assert result.endswith("whoami")
        assert "$HOME/go/bin" in result
        assert "$HOME/.local/bin" in result


class TestIsWafBlocked:
    def test_detects_known_waf_indicator(self):
        """Verify Detects known waf indicator."""
        runner = _make_runner()
        assert runner._is_waf_blocked("Sorry, IP address as possibly malicious was flagged") is True

    def test_clean_output_not_flagged(self):
        """Verify Clean output not flagged."""
        runner = _make_runner()
        assert runner._is_waf_blocked("200 OK, all clear") is False
