import pytest
from unittest.mock import MagicMock, patch
from app.tools.self_heal import SelfHealingService


@pytest.fixture
def healer():
    runner = MagicMock()
    runner.run.return_value = "Setting up tool..."
    return SelfHealingService(runner)


class TestHealthCheck:
    def test_returns_dict(self, healer):
        result = healer.health_check()
        assert isinstance(result, dict)
        assert "wsl" in result
        assert "ollama" in result
        assert "python" in result

    @patch("app.tools.self_heal.subprocess.run")
    def test_wsl_ok(self, mock_run, healer):
        mock_run.return_value = MagicMock(returncode=0, stdout="Default Distro: kali-linux", stderr="")
        result = healer.health_check()
        assert result["wsl"] == "ok"

    @patch("app.tools.self_heal.subprocess.run")
    def test_wsl_failed(self, mock_run, healer):
        mock_run.side_effect = FileNotFoundError()
        result = healer.health_check()
        assert "failed" in result["wsl"]

    @patch("app.tools.self_heal.urllib.request.urlopen")
    def test_ollama_ok(self, mock_urlopen, healer):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        result = healer.health_check()
        assert result["ollama"] == "ok"

    def test_python_ok(self, healer):
        result = healer.health_check()
        assert "ok" in result["python"]


class TestRestartService:
    def test_unknown_service(self, healer):
        result = healer.restart_service("unknown")
        assert "unknown" in result.lower()

    @patch("app.tools.self_heal.subprocess.run")
    @patch("app.tools.self_heal.subprocess.Popen")
    def test_restart_ollama(self, mock_popen, mock_run, healer):
        mock_run.return_value = MagicMock(returncode=0)
        mock_popen.return_value = MagicMock()
        result = healer.restart_service("ollama")
        assert "Successfully" in result

    @patch("app.tools.self_heal.subprocess.Popen")
    @patch("app.tools.self_heal.subprocess.run")
    def test_restart_ollama_not_found(self, mock_run, mock_popen, healer):
        mock_run.side_effect = FileNotFoundError("ollama.exe not found")
        mock_popen.side_effect = FileNotFoundError("ollama.exe not found in PATH")
        result = healer.restart_service("ollama")
        assert "not found" in result.lower()


class TestSystemSelfHeal:
    def test_pip_install(self, healer):
        with patch("app.tools.self_heal.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = healer.system_self_heal("pip install requests")
            assert "successfully installed" in result.lower()

    def test_pip_install_fails(self, healer):
        with patch("app.tools.self_heal.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = healer.system_self_heal("pip install requests")
            assert "failed" in result.lower()
