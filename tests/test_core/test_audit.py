"""Unit tests for the durable audit trail (app/core/audit.py, ARG-09)."""
import json

from app.core import audit


def test_log_event_appends_and_reads_back(tmp_path, monkeypatch):
    """Verify events append as JSON lines and read back oldest-first."""
    monkeypatch.setattr(audit, "AUDIT_PATH", str(tmp_path / "audit_log.jsonl"))
    assert audit.log_event("command", "agent", "example.com", "nikto -h x", "executed") is True
    assert audit.log_event("block", "safety-layer", "192.168.1.1", "x", "blocked", "private_ip") is True
    events = audit.read_events()
    assert len(events) == 2
    assert events[0]["kind"] == "command" and events[0]["status"] == "executed"
    assert events[1]["kind"] == "block" and events[1]["reason"] == "private_ip"


def test_log_event_truncates_long_fields(tmp_path, monkeypatch):
    """Verify command/target/reason fields are truncated to their caps."""
    monkeypatch.setattr(audit, "AUDIT_PATH", str(tmp_path / "audit_log.jsonl"))
    assert audit.log_event("command", "agent", "t" * 400, "c" * 900, "executed") is True
    ev = audit.read_events()[0]
    assert len(ev["target"]) == 200
    assert len(ev["command"]) == 500


def test_read_events_skips_corrupt_lines(tmp_path, monkeypatch):
    """Verify a corrupt line is skipped instead of poisoning the read."""
    path = tmp_path / "audit_log.jsonl"
    monkeypatch.setattr(audit, "AUDIT_PATH", str(path))
    audit.log_event("command", "agent", "t", "c", "executed")
    with open(path, "a", encoding="utf-8") as f:
        f.write("{corrupt\n")
    audit.log_event("block", "safety-layer", "t2", "c2", "blocked", "r")
    events = audit.read_events()
    assert len(events) == 2


def test_audit_file_is_jsonl(tmp_path, monkeypatch):
    """Verify the on-disk format stays one JSON object per line."""
    path = tmp_path / "audit_log.jsonl"
    monkeypatch.setattr(audit, "AUDIT_PATH", str(path))
    audit.log_event("command", "agent", "t", "c", "executed")
    audit.log_event("command", "agent", "t", "c", "executed")
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert all(json.loads(line)["kind"] == "command" for line in lines)
