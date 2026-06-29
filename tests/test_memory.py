import pytest
import tempfile
import os
import json
from app.core.memory.memory_service import ArgusMemory


@pytest.fixture
def db_path():
    tmp = tempfile.mktemp(suffix=".db")
    yield tmp
    if os.path.exists(tmp):
        os.remove(tmp)


@pytest.fixture
def mem(db_path):
    m = ArgusMemory(db_path=db_path)
    yield m
    m.clear_memory()


class TestArgusMemory:
    def test_init_creates_tables(self, db_path):
        m = ArgusMemory(db_path=db_path)
        with m._get_conn() as conn:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert "targets" in tables
        assert "findings" in tables
        assert "entities" in tables
        assert "relations" in tables
        assert "global_state" in tables

    def test_upsert_target_new(self, mem):
        mem.upsert_target("example.com")
        mem.add_finding("example.com", "test", "check", "ok", "verified")
        summary = json.loads(mem.get_blackboard_summary())
        assert "example.com" in summary

    def test_upsert_target_update_priority(self, mem):
        mem.upsert_target("example.com", priority=1)
        mem.upsert_target("example.com", priority=5)
        with mem._get_conn() as conn:
            row = conn.execute(
                "SELECT priority FROM targets WHERE domain = ?", ("example.com",)
            ).fetchone()
        assert row["priority"] == 5

    def test_add_finding_auto_upserts_target(self, mem):
        mem.add_finding("newdomain.com", "nmap", "ports", "80/tcp", "HTTP")
        summary = json.loads(mem.get_blackboard_summary())
        assert "newdomain.com" in summary
        assert summary["newdomain.com"]["ports"] == "HTTP"

    def test_add_finding_multiple_types(self, mem):
        mem.add_finding("x.com", "nmap", "ports", "80/tcp", "HTTP")
        mem.add_finding("x.com", "whatweb", "tech", "nginx", "Nginx 1.24")
        summary = json.loads(mem.get_blackboard_summary())
        assert summary["x.com"]["ports"] == "HTTP"
        assert summary["x.com"]["tech"] == "Nginx 1.24"

    def test_upsert_entity_new(self, mem):
        eid = mem.upsert_entity("ip", "10.0.0.1")
        assert eid > 0

    def test_upsert_entity_duplicate(self, mem):
        eid1 = mem.upsert_entity("ip", "10.0.0.1")
        eid2 = mem.upsert_entity("ip", "10.0.0.1", {"region": "us-east"})
        assert eid1 == eid2

    def test_upsert_entity_with_metadata(self, mem):
        mem.upsert_entity("tech", "nginx", {"version": "1.24", "cve": "CVE-2024-1234"})
        with mem._get_conn() as conn:
            row = conn.execute(
                "SELECT metadata FROM entities WHERE value = ?", ("nginx",)
            ).fetchone()
        meta = json.loads(row["metadata"])
        assert meta["version"] == "1.24"

    def test_add_relation(self, mem):
        mem.upsert_entity("ip", "10.0.0.1")
        mem.upsert_entity("tech", "nginx")
        mem.add_relation("10.0.0.1", "nginx", "USES_TECH")
        insights = mem.get_graph_insights()
        assert "(10.0.0.1) --[USES_TECH]--> (nginx)" in insights

    def test_add_relation_missing_entities(self, mem):
        mem.add_relation("ghost-a", "ghost-b", "LINKED_TO")
        assert mem.get_graph_insights() == ""

    def test_get_graph_insights_empty(self, mem):
        assert mem.get_graph_insights() == ""

    def test_get_blackboard_summary_empty(self, mem):
        assert mem.get_blackboard_summary() == "{}"

    def test_clear_memory(self, mem):
        mem.upsert_target("example.com")
        mem.clear_memory()
        assert mem.get_blackboard_summary() == "{}"

    def test_clear_memory_then_reuse(self, mem):
        mem.upsert_target("example.com")
        mem.add_finding("example.com", "test", "check", "ok", "old")
        mem.clear_memory()
        mem.upsert_target("new.com")
        mem.add_finding("new.com", "test", "check", "ok", "new")
        summary = json.loads(mem.get_blackboard_summary())
        assert "new.com" in summary
        assert "example.com" not in summary

    def test_multiple_targets_blackboard(self, mem):
        mem.upsert_target("a.com", priority=1)
        mem.upsert_target("b.com", priority=5)
        mem.add_finding("a.com", "tool", "type1", "raw", "sum_a")
        mem.add_finding("b.com", "tool", "type2", "raw", "sum_b")
        summary = json.loads(mem.get_blackboard_summary())
        assert "a.com" in summary
        assert "b.com" in summary

    @pytest.mark.slow
    def test_large_insert_performance(self, db_path):
        m = ArgusMemory(db_path=db_path)
        for i in range(1000):
            m.upsert_target(f"target{i}.com", priority=i % 10)
            m.add_finding(
                f"target{i}.com", "nmap", "ports", f"{i}", f"port {i}"
            )
        import time
        start = time.time()
        summary = m.get_blackboard_summary()
        elapsed = time.time() - start
        assert elapsed < 2.0, f"get_blackboard_summary took {elapsed:.2f}s"
        parsed = json.loads(summary)
        assert len(parsed) == 1000

    def test_upsert_target_null_parent(self, mem):
        mem.upsert_target("root.com")
        mem.upsert_target("sub.root.com", parent_domain="root.com")
        with mem._get_conn() as conn:
            row = conn.execute(
                "SELECT parent_domain FROM targets WHERE domain = ?",
                ("sub.root.com",),
            ).fetchone()
        assert row["parent_domain"] == "root.com"

    def test_entity_returns_negative_on_failure(self, mem):
        eid = mem.upsert_entity("", None)
        assert eid == -1

    def test_unicode_finding(self, mem):
        mem.add_finding("пример.рф", "tool", "test", "raw", "unicode тест")
        summary = json.loads(mem.get_blackboard_summary())
        assert "пример.рф" in summary

    def test_schema_version(self, db_path):
        m = ArgusMemory(db_path=db_path)
        version = m._get_schema_version()
        assert version > 0
