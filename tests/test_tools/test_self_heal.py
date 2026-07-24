import pytest
from unittest.mock import MagicMock, patch
from app.tools.self_heal import SelfHealingService

pytestmark = pytest.mark.unit


@pytest.fixture
def healer():
    """Build a SelfHealingService with a mocked runner stubbed to a generic success message.

    Returns:
        SelfHealingService: Configured with the mocked runner.
    """
    runner = MagicMock()
    runner.run.return_value = "Setting up tool..."
    return SelfHealingService(runner)


class TestHealthCheck:
    def test_returns_dict(self, healer):
        """Verify Returns dict.
        
        Args:
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = healer.health_check()
        assert isinstance(result, dict)
        assert "wsl" in result
        assert "ollama" in result
        assert "python" in result

    @patch("app.tools.self_heal.subprocess.run")
    def test_wsl_ok(self, mock_run, healer):
        """Verify Wsl ok.
        
        Args:
            mock_run: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="Default Distro: kali-linux", stderr="")
        result = healer.health_check()
        assert result["wsl"] == "ok"

    @patch("app.tools.self_heal.subprocess.run")
    def test_wsl_failed(self, mock_run, healer):
        """Verify Wsl failed.
        
        Args:
            mock_run: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        mock_run.side_effect = FileNotFoundError()
        result = healer.health_check()
        assert "failed" in result["wsl"]

    @patch("app.tools.self_heal.urllib.request.urlopen")
    def test_ollama_ok(self, mock_urlopen, healer):
        """Verify Ollama ok.
        
        Args:
            mock_urlopen: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        result = healer.health_check()
        assert result["ollama"] == "ok"

    def test_python_ok(self, healer):
        """Verify Python ok.
        
        Args:
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = healer.health_check()
        assert "ok" in result["python"]


class TestRestartService:
    def test_unknown_service(self, healer):
        """Verify Unknown service.
        
        Args:
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = healer.restart_service("unknown")
        assert "unknown" in result.lower()

    @patch("app.tools.self_heal.subprocess.run")
    @patch("app.tools.self_heal.subprocess.Popen")
    def test_restart_ollama(self, mock_popen, mock_run, healer):
        """Verify Restart ollama.
        
        Args:
            mock_popen: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
            mock_run: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        mock_run.return_value = MagicMock(returncode=0)
        mock_popen.return_value = MagicMock()
        result = healer.restart_service("ollama")
        assert "Successfully" in result

    @patch("app.tools.self_heal.subprocess.Popen")
    @patch("app.tools.self_heal.subprocess.run")
    def test_restart_ollama_not_found(self, mock_run, mock_popen, healer):
        """Verify Restart ollama not found.
        
        Args:
            mock_run: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
            mock_popen: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
            healer: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        mock_run.side_effect = FileNotFoundError("ollama.exe not found")
        mock_popen.side_effect = FileNotFoundError("ollama.exe not found in PATH")
        result = healer.restart_service("ollama")
        assert "not found" in result.lower()


class TestSystemSelfHeal:
    def test_pip_install(self, healer):
        """Verify Pip install."""
        with patch("app.tools.self_heal.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = healer.system_self_heal("pip install requests")
            assert "successfully installed" in result.lower()

    def test_pip_install_uses_list_form_not_shell_string(self, healer):
        """Regression test for a real command-injection vulnerability found
        and fixed (2026-07-19, opencode-delegate review): system_self_heal()
        used to build a shell string and run it with `shell=True`, letting an
        LLM-tool-call-derived package name inject arbitrary shell commands.
        The fix passes argv as a list with no shell involved - this locks
        that in, rather than trusting a mocked "it returned success" alone.

        Args:
            healer: test parameter provided by this test's own setup (a
                pytest fixture or a mock/patch injected via a decorator -
                see the test's parameters/decorators for which).
        """
        malicious_package = "innocuous;$(touch${IFS}/tmp/pwned)"
        with patch("app.tools.self_heal.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            healer.system_self_heal(f"pip install {malicious_package}")

            args, kwargs = mock_run.call_args
            command = args[0]
            assert isinstance(command, list), (
                "subprocess.run must receive argv as a list, not a shell string"
            )
            assert not kwargs.get("shell", False), (
                "subprocess.run must not use shell=True - it re-enables the "
                "exact injection this fix closed"
            )
            # The malicious text must survive as one literal, unexecuted argv
            # element - proof it was never hits a shell to interpret ; or $().
            assert malicious_package in command

    def test_pip_install_fails(self, healer):
        """Verify Pip install fails."""
        with patch("app.tools.self_heal.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = healer.system_self_heal("pip install requests")
            assert "failed" in result.lower()
