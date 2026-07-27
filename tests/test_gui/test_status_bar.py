import socket
from unittest.mock import patch

import pytest

from app.GUI.components.status_bar import check_ollama_status, check_ssh_status

pytestmark = pytest.mark.unit


class TestCheckOllamaStatus:
    def test_returns_true_when_port_open(self):
        """Verify Returns true when port open."""
        check_ollama_status.clear()
        with patch("socket.socket") as mock_socket_cls:
            mock_socket_cls.return_value.connect_ex.return_value = 0
            assert check_ollama_status() is True

    def test_returns_false_when_port_closed(self):
        """Verify Returns false when port closed."""
        check_ollama_status.clear()
        with patch("socket.socket") as mock_socket_cls:
            mock_socket_cls.return_value.connect_ex.return_value = 1
            assert check_ollama_status() is False


class TestCheckSshStatus:
    """Regression test: this previously spawned a whole new powershell.exe
    process (Test-NetConnection) on every call, and render_status_bar()
    calling it on every single click/tab-switch (Streamlit reruns the whole
    script on any widget interaction) made the entire GUI feel heavy - a
    user live-reported "the GUI itself feels heavy/slow when clicking or
    navigating tabs". Now uses the same lightweight raw socket connect
    check_ollama_status() already used - no process spawn."""

    def test_uses_raw_socket_not_a_subprocess(self):
        """Verify Uses raw socket not a subprocess."""
        check_ssh_status.clear()
        with patch("socket.socket") as mock_socket_cls, patch("subprocess.run") as mock_run:
            mock_socket_cls.return_value.connect_ex.return_value = 0
            result = check_ssh_status()
            assert result is True
            mock_run.assert_not_called()

    def test_returns_true_when_port_open(self):
        """Verify Returns true when port open."""
        check_ssh_status.clear()
        with patch("socket.socket") as mock_socket_cls:
            mock_socket_cls.return_value.connect_ex.return_value = 0
            assert check_ssh_status() is True

    def test_returns_false_when_port_closed(self):
        """Verify Returns false when port closed."""
        check_ssh_status.clear()
        with patch("socket.socket") as mock_socket_cls:
            mock_socket_cls.return_value.connect_ex.return_value = 1
            assert check_ssh_status() is False

    def test_returns_false_on_socket_exception(self):
        """Verify Returns false on socket exception."""
        check_ssh_status.clear()
        with patch("socket.socket", side_effect=OSError("boom")):
            assert check_ssh_status() is False
