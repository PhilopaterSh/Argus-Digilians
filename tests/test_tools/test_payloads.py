from unittest.mock import MagicMock

from app.tools.payloads import fetch_intruder_payloads


class TestFetchIntruderPayloads:
    def test_returns_parsed_lines_on_success(self):
        runner = MagicMock()
        runner.run.return_value = "../../../../etc/passwd\n..%2f..%2fetc%2fpasswd\n"

        result = fetch_intruder_payloads(runner, "path_traversal")

        assert result == ["../../../../etc/passwd", "..%2f..%2fetc%2fpasswd"]

    def test_unknown_vulnerability_type_returns_empty_without_running_a_command(self):
        runner = MagicMock()

        result = fetch_intruder_payloads(runner, "xss")

        assert result == []
        runner.run.assert_not_called()

    def test_missing_local_mirror_fails_soft(self):
        """A fresh install that hasn't cloned PayloadsAllTheThings into Kali
        WSL yet must not break advanced_vuln_probe() - fail soft (empty
        list), not raise."""
        runner = MagicMock()
        runner.run.return_value = "cat: /opt/payloads/...: No such file or directory"

        result = fetch_intruder_payloads(runner, "sqli")

        assert result == []

    def test_empty_response_returns_empty_list(self):
        runner = MagicMock()
        runner.run.return_value = ""

        result = fetch_intruder_payloads(runner, "sqli")

        assert result == []

    def test_strips_blank_lines(self):
        runner = MagicMock()
        runner.run.return_value = "payload_one\n\n  \npayload_two\n"

        result = fetch_intruder_payloads(runner, "sqli")

        assert result == ["payload_one", "payload_two"]

    def test_respects_limit_in_shuf_command(self):
        runner = MagicMock()
        runner.run.return_value = ""

        fetch_intruder_payloads(runner, "sqli", limit=7)

        cmd = runner.run.call_args[0][0]
        assert "shuf -n 7" in cmd
