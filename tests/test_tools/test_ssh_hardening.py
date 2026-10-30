"""SSH hardening tests: host-key pinning + key-auth wiring (ARG-02/07)."""
import paramiko
import pytest

from app.tools import command_runner as cr
from app.tools.wsl_bridge import WSLConfig


def test_fingerprint_policy_accepts_matching_key():
    """Verify the pinned-fingerprint policy accepts the exact key."""
    key = paramiko.RSAKey.generate(2048)
    import base64
    import hashlib
    fp = "sha256:" + base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip("=")
    policy = cr._FingerprintPolicy(fp)
    policy.missing_host_key(None, "127.0.0.1", key)  # must not raise


def test_fingerprint_policy_rejects_substituted_key():
    """Verify a substituted host key is rejected (MITM protection)."""
    key = paramiko.RSAKey.generate(2048)
    policy = cr._FingerprintPolicy("sha256:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    with pytest.raises(paramiko.SSHException):
        policy.missing_host_key(None, "127.0.0.1", key)


def test_config_reads_ssh_hardening_env(monkeypatch):
    """Verify WSLConfig picks up the two hardening env vars."""
    monkeypatch.setenv("WSL_KEY_PATH", "~/.ssh/id_ed25519")
    monkeypatch.setenv("WSL_HOST_KEY_SHA256", "sha256:AbCdEf")
    cfg = WSLConfig()
    assert cfg.key_path == "~/.ssh/id_ed25519"
    assert cfg.host_key_sha256 == "sha256:AbCdEf"


def test_run_ssh_uses_key_filename_when_configured(monkeypatch):
    """Verify _run_ssh passes key_filename to paramiko when a key is set."""
    captured = {}

    class FakeClient:
        def set_missing_host_key_policy(self, policy):
            captured["policy"] = policy

        def connect(self, host, **kwargs):
            captured["host"] = host
            captured["kwargs"] = kwargs

        def exec_command(self, command, timeout=None):
            class Ch:
                def settimeout(self, t):
                    pass

            import io

            return io.StringIO("out"), io.StringIO(""), Ch()

        def close(self):
            pass

    bridge = type("B", (), {})()
    bridge.config = WSLConfig(
        host="203.0.113.5",
        user="kali",
        password="pw",
        port=22,
        key_path="~/.ssh/id_ed25519",
        host_key_sha256="",
    )
    bridge.ensure_ssh_service = lambda: True
    runner = cr.CommandRunner(bridge)
    monkeypatch.setattr(cr.paramiko, "SSHClient", FakeClient)
    out = runner._run_ssh("echo hi")
    assert captured["kwargs"]["key_filename"] == "~/.ssh/id_ed25519"
    assert "hi" in out or out == "out"
