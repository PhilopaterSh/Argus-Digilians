import pytest
from unittest.mock import MagicMock
from app.tools.reflective_verification import ReflectiveVerificationService

pytestmark = pytest.mark.unit


@pytest.fixture
def verifier():
    runner = MagicMock()
    memory = MagicMock()
    memory.get_blackboard_summary.return_value = "{}"
    return ReflectiveVerificationService(runner, memory)


class TestPreExecuteVerify:
    def test_empty_command(self, verifier):
        """Verify Empty command.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("")
        assert "empty" in result.lower()

    def test_whitespace_command(self, verifier):
        """Verify Whitespace command.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("   ")
        assert "empty" in result.lower()

    def test_blacklist_rm_rf(self, verifier):
        """Verify Blacklist rm rf.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("; rm -rf /")
        assert "blocked" in result.lower()

    def test_blacklist_double_pipe_rm(self, verifier):
        """Verify Blacklist double pipe rm.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("|| rm -rf")
        assert "blocked" in result.lower()

    def test_nmap_without_target(self, verifier):
        """Verify Nmap without target.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("nmap")
        assert "missing" in result.lower()

    def test_nmap_with_target(self, verifier):
        """Verify Nmap with target.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("nmap -sV example.com")
        assert "success" in result.lower()

    def test_curl_without_url(self, verifier):
        """Verify Curl without url.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("curl something")
        assert "missing" in result.lower()

    def test_curl_with_url(self, verifier):
        """Verify Curl with url.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("curl http://example.com")
        assert "success" in result.lower()

    def test_valid_command(self, verifier):
        """Verify Valid command.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.pre_execute_verify("whoami")
        assert "success" in result.lower()

    def test_infinite_loop_detection(self, verifier):
        """Verify Infinite loop detection.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        cmd = "nmap -sV test.com"
        r1 = verifier.pre_execute_verify(cmd)
        assert "success" in r1.lower()
        r2 = verifier.pre_execute_verify(cmd)
        assert "success" in r2.lower()
        r3 = verifier.pre_execute_verify(cmd)
        assert "blocked" in r3.lower()
        assert "loop" in r3.lower()

    def test_different_commands_no_loop(self, verifier):
        """Verify Different commands no loop.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        verifier.pre_execute_verify("cmd1")
        verifier.pre_execute_verify("cmd2")
        r3 = verifier.pre_execute_verify("cmd3")
        assert "success" in r3.lower()


class TestPostExecuteVerify:
    def test_empty_output(self, verifier):
        """Verify Empty output.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.post_execute_verify("http://x.com", "cmd", "")
        assert "empty" in result.lower()

    def test_waf_detection(self, verifier):
        """Verify Waf detection.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.post_execute_verify("http://x.com", "cmd", "cloudflare error 403 forbidden")
        assert "waf" in result.lower() or "blocked" in result.lower()

    def test_false_positive_redirect(self, verifier):
        """Verify False positive redirect.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.post_execute_verify(
            "http://x.com", "curl -v", "HTTP/1.1 302\nlocation: / "
        )
        assert "false positive" in result.lower()

    def test_content_length_zero(self, verifier):
        """Verify Content length zero.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.post_execute_verify(
            "http://x.com", "curl", "HTTP/1.1 200\nContent-Length: 0"
        )
        assert "false positive" in result.lower()

    def test_sensitive_data_found(self, verifier):
        """Verify Sensitive data found.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.post_execute_verify(
            "http://x.com", "cat /etc/passwd", "root:x:0:0:"
        )
        assert "SUCCESS" in result.upper()
        assert "confirmed" in result.lower()

    def test_no_issues(self, verifier):
        """Verify No issues.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.post_execute_verify(
            "http://x.com", "ls", "file1\nfile2"
        )
        assert "no immediate" in result.lower()


class TestTaskDifficultyAssessment:
    def test_empty_targets(self, verifier):
        """Verify Empty targets.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.task_difficulty_assessment("")
        assert "error" in result.lower()

    def test_single_target(self, verifier):
        """Verify Single target.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.task_difficulty_assessment("example.com")
        assert "TDA" in result
        assert "example.com" in result

    def test_multiple_targets(self, verifier):
        """Verify Multiple targets.
        
        Args:
            verifier: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        result = verifier.task_difficulty_assessment("a.com, b.com")
        assert "a.com" in result
        assert "b.com" in result
