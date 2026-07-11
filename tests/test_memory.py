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

        # specs/018-structured-agent-reliability: get_blackboard_summary()'s
        # default is now bounded (max_chars=3000) - unbounded growth across
        # every target ever scanned is exactly what fed an oversized prompt
        # into a live agent run and crashed the GPU process. Default call
        # must stay well within the bound, not return all 1000 targets.
        start = time.time()
        bounded_summary = m.get_blackboard_summary()
        bounded_elapsed = time.time() - start
        assert bounded_elapsed < 2.0, f"get_blackboard_summary took {bounded_elapsed:.2f}s"
        assert len(bounded_summary) <= 3000
        bounded_parsed = json.loads(bounded_summary)
        assert 0 < len(bounded_parsed) < 1000

        # Explicitly requesting a large-enough budget still performs well
        # and returns everything - the bound is a default, not a hard cap.
        start = time.time()
        full_summary = m.get_blackboard_summary(max_chars=1_000_000)
        full_elapsed = time.time() - start
        assert full_elapsed < 2.0, f"get_blackboard_summary(max_chars=1_000_000) took {full_elapsed:.2f}s"
        assert len(json.loads(full_summary)) == 1000

    def test_summarize_for_planning_empty(self, mem):
        assert mem.summarize_for_planning() == "No shared memory available."

    def test_summarize_for_planning_bounds_per_source_not_globally(self, mem):
        """specs/019 SC-003: 3 sources x 5 findings each -> exactly the last
        k=3 per (domain, tool_name) group, not the last 9 overall."""
        mem.upsert_target("x.com")
        for source in ("nmap", "whatweb", "nikto"):
            for i in range(5):
                mem.add_finding("x.com", source, "type1", f"raw{i}", f"{source}-finding-{i}")
        summary = mem.summarize_for_planning(k=3)
        lines = summary.split("\n")
        assert len(lines) == 9, f"expected 9 lines (3 sources x k=3), got {len(lines)}"
        for source in ("nmap", "whatweb", "nikto"):
            source_lines = [l for l in lines if l.startswith(f"[{source}]")]
            assert len(source_lines) == 3, f"{source} should contribute exactly 3 lines, got {len(source_lines)}"
            # Most recent 3 (finding-2, finding-3, finding-4) must be kept, not the oldest 3.
            kept_indices = {int(l.rsplit("-", 1)[1]) for l in source_lines}
            assert kept_indices == {2, 3, 4}, f"{source} kept the wrong findings: {kept_indices}"

    def test_summarize_for_planning_formats_with_source_prefix(self, mem):
        mem.upsert_target("y.com")
        mem.add_finding("y.com", "nikto", "vuln", "raw", "found XSS")
        summary = mem.summarize_for_planning()
        assert summary == "[nikto] y.com vuln: found XSS"

    def test_summarize_for_planning_respects_max_chars(self, mem):
        mem.upsert_target("z.com")
        for i in range(50):
            mem.add_finding("z.com", f"tool{i}", "type1", "raw", "x" * 100)
        summary = mem.summarize_for_planning(k=3, max_chars=500)
        assert len(summary) <= 500

    def test_get_blackboard_summary_unaffected_by_summarize_for_planning(self, mem):
        """specs/019: the new method is additive - get_blackboard_summary()'s
        existing domain->data_type shape (relied on by test_add_finding_multiple_types
        et al.) must be completely unchanged."""
        mem.add_finding("x.com", "nmap", "ports", "80/tcp", "HTTP")
        mem.add_finding("x.com", "whatweb", "tech", "nginx", "Nginx 1.24")
        summary = json.loads(mem.get_blackboard_summary())
        assert summary["x.com"]["ports"] == "HTTP"
        assert summary["x.com"]["tech"] == "Nginx 1.24"

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
        mem.add_finding("\u043f\u0440\u0438\u043c\u0435\u0440.\u0440\u0444", "tool", "test", "raw", "unicode \u0442\u0435\u0441\u0442")
        summary = json.loads(mem.get_blackboard_summary())
        assert "\u043f\u0440\u0438\u043c\u0435\u0440.\u0440\u0444" in summary

    def test_schema_version(self, db_path):
        m = ArgusMemory(db_path=db_path)
        version = m._get_schema_version()
        assert version > 0
