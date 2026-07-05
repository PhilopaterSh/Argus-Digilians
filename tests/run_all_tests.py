"""
Argus Master Test Runner - Validates all modules.
Runs import checks, unit tests, and integration checks.
"""
import sys
import os
import traceback
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = []


def test(name, func):
    try:
        func()
        print(f"{PASS} {name}")
        results.append((name, True, None))
    except Exception as e:
        print(f"{FAIL} {name}: {e}")
        results.append((name, False, str(e)))


# ─── IMPORT TESTS ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(" ARGUS TEST SUITE v2.0")
print("=" * 60)
print("\n--- Module Import Tests ---")

test("Import: core.safety", lambda: __import__('core.safety'))
test("Import: core.schemas", lambda: __import__('core.schemas'))
test("Import: core.memory", lambda: __import__('core.memory'))
test("Import: core.agent", lambda: __import__('core.agent'))
test("Import: core.tools", lambda: __import__('core.tools'))
test("Import: reports.report_engine", lambda: __import__('reports.report_engine'))
test("Import: plugins", lambda: __import__('plugins'))
test("Import: plugins.base_plugin", lambda: __import__('plugins.base_plugin'))
test("Import: plugins.scanner_plugin", lambda: __import__('plugins.scanner_plugin'))
test("Import: plugins.fuzzer_plugin", lambda: __import__('plugins.fuzzer_plugin'))

# ─── SAFETY LAYER TESTS ───────────────────────────────────────────────────
print("\n--- Safety Layer Tests ---")
from core.safety import SafetyLayer

def test_block_rm_rf():
    s = SafetyLayer()
    assert s.is_destructive_payload("rm -rf /") == True

def test_block_drop_table():
    s = SafetyLayer()
    assert s.is_destructive_payload("DROP TABLE users") == True

def test_allow_safe_cmd():
    s = SafetyLayer()
    assert s.is_destructive_payload("nmap -Pn example.com") == False

def test_sanitize_input():
    s = SafetyLayer()
    result = s.sanitize_input("test$(evil)input")
    assert "$(" not in result

def test_validate_target_valid():
    s = SafetyLayer()
    ok, msg = s.validate_target("https://example.com")
    assert ok == True

def test_validate_target_private_ip():
    s = SafetyLayer(allow_internal=False)
    ok, msg = s.validate_target("http://192.168.1.1")
    assert ok == False

test("Safety: Block rm -rf", test_block_rm_rf)
test("Safety: Block DROP TABLE", test_block_drop_table)
test("Safety: Allow safe nmap", test_allow_safe_cmd)
test("Safety: Sanitize injection chars", test_sanitize_input)
test("Safety: Validate public target", test_validate_target_valid)
test("Safety: Block private IP", test_validate_target_private_ip)

# ─── MEMORY TESTS ──────────────────────────────────────────────────────────
print("\n--- Memory (SQLite) Tests ---")
import tempfile
from core.memory import ArgusMemory

def test_memory_init():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = f.name
    mem = ArgusMemory(db_path=db)
    assert mem.db_path == db
    os.unlink(db)

def test_memory_upsert_target():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = f.name
    mem = ArgusMemory(db_path=db)
    mem.upsert_target("example.com")
    summary = mem.get_blackboard_summary()
    os.unlink(db)

def test_memory_add_finding():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = f.name
    mem = ArgusMemory(db_path=db)
    mem.upsert_target("example.com")
    mem.add_finding("example.com", "nmap", "ports", "80/tcp open", "Port 80 open")
    summary = mem.get_blackboard_summary()
    assert "example.com" in summary
    os.unlink(db)

def test_memory_graph():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = f.name
    mem = ArgusMemory(db_path=db)
    mem.upsert_entity("domain", "example.com")
    mem.upsert_entity("ip", "1.2.3.4")
    mem.add_relation("example.com", "1.2.3.4", "HOSTS")
    insights = mem.get_graph_insights()
    assert "HOSTS" in insights
    os.unlink(db)

def test_memory_scan_log():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db = f.name
    mem = ArgusMemory(db_path=db)
    mem.log_scan_session("example.com", "passive", "2026-01-01", "2026-01-01", 5, 7)
    history = mem.get_scan_history()
    assert len(history) == 1
    os.unlink(db)

test("Memory: Init DB", test_memory_init)
test("Memory: Upsert target", test_memory_upsert_target)
test("Memory: Add finding", test_memory_add_finding)
test("Memory: Knowledge graph relations", test_memory_graph)
test("Memory: Log scan session", test_memory_scan_log)

# ─── SCHEMA TESTS ─────────────────────────────────────────────────────────
print("\n--- Schema Tests ---")
from core.schemas import SecurityReport, Finding, PluginResult

def test_schema_finding():
    f = Finding(target="example.com", issue="XSS", severity="High",
                description="XSS found", remediation="Sanitize input")
    assert f.target == "example.com"

def test_schema_report():
    r = SecurityReport(
        summary="Test", attack_surface_stats="1 subdomain",
        findings=[], overall_risk_score=5, next_steps=["Patch"]
    )
    assert r.overall_risk_score == 5

def test_schema_plugin_result():
    pr = PluginResult(plugin_name="test", target="example.com", success=True, output="ok")
    assert pr.success == True

test("Schema: Finding model", test_schema_finding)
test("Schema: SecurityReport model", test_schema_report)
test("Schema: PluginResult model", test_schema_plugin_result)

# ─── REPORT ENGINE TESTS ─────────────────────────────────────────────────
print("\n--- Report Engine Tests ---")
import tempfile
from reports.report_engine import ReportEngine

def test_report_engine_generate():
    with tempfile.TemporaryDirectory() as tmpdir:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db = f.name
        mem = ArgusMemory(db_path=db)
        mem.upsert_target("example.com")
        mem.add_finding("example.com", "nmap", "ports", "443/tcp open", "HTTPS open", severity="Info")
        engine = ReportEngine(mem, tmpdir)
        json_path, md_path, score = engine.generate("example.com", "passive")
        assert Path(json_path).exists()
        assert Path(md_path).exists()
        assert 1 <= score <= 10
        os.unlink(db)

def test_severity_score():
    engine = ReportEngine(None, "/tmp")
    findings = [
        {"severity": "Critical"}, {"severity": "High"}, {"severity": "Medium"}
    ]
    score = engine.severity_score(findings)
    assert 1 <= score <= 10

test("ReportEngine: Generate JSON+MD", test_report_engine_generate)
test("ReportEngine: Severity score", test_severity_score)

# ─── PLUGIN TESTS ─────────────────────────────────────────────────────────
print("\n--- Plugin System Tests ---")
from plugins import list_plugins, PLUGIN_REGISTRY
from plugins.scanner_plugin import ScannerPlugin
from plugins.fuzzer_plugin import FuzzerPlugin

def test_plugin_registry():
    plugins = list_plugins()
    assert "scanner" in plugins
    assert "fuzzer" in plugins

def test_scanner_dry_run():
    p = ScannerPlugin()
    result = p.dry_run("example.com")
    assert result.success == True

def test_fuzzer_dry_run():
    p = FuzzerPlugin()
    result = p.dry_run("example.com")
    assert result.success == True

test("Plugins: Registry has scanner and fuzzer", test_plugin_registry)
test("Plugin: Scanner dry run", test_scanner_dry_run)
test("Plugin: Fuzzer dry run", test_fuzzer_dry_run)

# ─── RESULTS SUMMARY ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f" RESULTS: {passed} passed | {failed} failed | {len(results)} total")
print("=" * 60)

if failed > 0:
    print("\nFailed tests:")
    for name, ok, err in results:
        if not ok:
            print(f"  {FAIL} {name}: {err}")
    sys.exit(1)
else:
    print("\n\033[92m ALL TESTS PASSED! \033[0m")
    sys.exit(0)
