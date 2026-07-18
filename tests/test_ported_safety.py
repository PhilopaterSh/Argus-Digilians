"""Ported tests from momen — SafetyLayer + ArgusMemory entity operations."""
import pytest
import json
import tempfile
import os
import sqlite3

from app.core.safety import SafetyLayer
from app.core.memory.memory_service import ArgusMemory


class TestSafetyLayerPorted:
    def test_validate_https_url(self):
        sl = SafetyLayer()
        v, r = sl.validate_target("https://example.com", "aggressive")
        assert v, r

    def test_validate_bare_domain(self):
        sl = SafetyLayer()
        v, r = sl.validate_target("sketchfab.com", "aggressive")
        assert v, r

    def test_validate_wildcard_pattern(self):
        sl = SafetyLayer()
        v, r = sl.validate_target("*.example.com", "aggressive")
        assert v, r

    def test_validate_dir_wildcard(self):
        sl = SafetyLayer()
        v, r = sl.validate_target("example.com/*/*/*", "aggressive")
        assert v, r

    def test_validate_private_ip_blocked(self):
        sl = SafetyLayer()
        v, r = sl.validate_target("192.168.1.1", "aggressive")
        assert not v
        assert "private range" in r.lower()

    def test_destructive_payload_detected(self):
        sl = SafetyLayer()
        assert sl.is_destructive_payload("rm -rf /")

    def test_nmap_allowed(self):
        sl = SafetyLayer()
        assert not sl.is_destructive_payload("nmap -sV example.com")

    def test_destructive_payload_drop_table(self):
        sl = SafetyLayer()
        assert sl.is_destructive_payload("DROP TABLE users")

    def test_sanitize_removes_null_bytes(self):
        sl = SafetyLayer()
        assert sl.sanitize_input("test\x00payload") == "testpayload"

    def test_sanitize_removes_shell_chars(self):
        sl = SafetyLayer()
        assert "`" not in sl.sanitize_input("`rm -rf /`")
        assert "$(" not in sl.sanitize_input("$(whoami)")

    def test_guard_command_blocks_destructive(self):
        sl = SafetyLayer()
        safe, reason = sl.guard_command("rm -rf /etc")
        assert not safe

    def test_guard_command_permits_safe(self):
        sl = SafetyLayer()
        safe, reason = sl.guard_command("nmap -sV target")
        assert safe

    def test_audit_log_tracks_blocks(self):
        sl = SafetyLayer()
        sl.is_destructive_payload("rm -rf /")
        sl.is_destructive_payload("mkfs.ext4 /dev/sda1")
        assert sl.get_stats()["total_blocked"] == 2
        assert len(sl.get_audit_log()) == 2

    def test_allow_internal_bypasses_private_check(self):
        sl = SafetyLayer(allow_internal=True)
        v, r = sl.validate_target("192.168.1.1", "aggressive")
        assert v, r

    def test_validate_empty_url(self):
        sl = SafetyLayer()
        v, r = sl.validate_target("", "passive")
        assert not v


class TestMemoryPorted:
    @pytest.fixture
    def db_path(self):
        tmp = tempfile.mktemp(suffix=".db")
        yield tmp
        if os.path.exists(tmp):
            os.remove(tmp)

    @pytest.fixture
    def mem(self, db_path):
        m = ArgusMemory(db_path=db_path)
        yield m
        m.clear_memory()

    def test_upsert_entity_returns_id(self, mem):
        eid = mem.upsert_entity("ip", "1.2.3.4", {"asn": "AS12345"})
        assert isinstance(eid, int)
        assert eid > 0

    def test_add_relation(self, mem):
        mem.upsert_entity("domain", "test.example.com")
        mem.upsert_entity("ip", "1.2.3.4")
        mem.add_relation("test.example.com", "1.2.3.4", "resolves_to")
        insights = mem.get_graph_insights()
        assert isinstance(insights, str)
        assert "1.2.3.4" in insights

    def test_target_priority_persists(self, mem):
        mem.upsert_target("alpha.com", priority=5)
        mem.upsert_target("beta.com", priority=1)
        with mem._get_conn() as conn:
            rows = conn.execute(
                "SELECT domain, priority FROM targets ORDER BY priority DESC"
            ).fetchall()
        domains = [r["domain"] for r in rows]
        assert domains == ["alpha.com", "beta.com"]

    def test_upsert_target_then_finding(self, mem):
        mem.upsert_target("test.example.com", parent_domain="example.com", priority=5)
        mem.add_finding("test.example.com", "XSS", "xss", "<script>", "Reflected XSS found")
        bb = json.loads(mem.get_blackboard_summary())
        assert "test.example.com" in bb
        assert bb["test.example.com"]["xss"] == "Reflected XSS found"
