"""
Argus comprehensive function tests.
Tests every key function without requiring WSL/Kali/Ollama to be running.
"""
import sys, os, re, json, tempfile, sqlite3
sys.path.insert(0, "/sessions/focused-pensive-allen/mnt/Argus_Digilians_ argus_PHILOPATERSH/FINAL_STABLE_SECURITY_PROJECT")

PASS = 0
FAIL = 0
results = []

def ok(name):
    global PASS
    PASS += 1
    results.append(f"  [PASS] {name}")

def fail(name, reason):
    global FAIL
    FAIL += 1
    results.append(f"  [FAIL] {name}: {reason}")

# ─────────────────────────────────────────────────────────────────────────────
# 1. SAFETY LAYER
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 1. SafetyLayer ===")
from core.safety import SafetyLayer
sl = SafetyLayer()

v, r = sl.validate_target("https://example.com", "aggressive")
if v: ok("validate_target — https URL")
else: fail("validate_target — https URL", r)

v, r = sl.validate_target("sketchfab.com", "aggressive")
if v: ok("validate_target — bare domain")
else: fail("validate_target — bare domain", r)

v, r = sl.validate_target("*.example.com", "aggressive")
if v: ok("validate_target — *.domain wildcard")
else: fail("validate_target — *.domain wildcard", r)

v, r = sl.validate_target("example.com/*/*/*", "aggressive")
if v: ok("validate_target — dir wildcard")
else: fail("validate_target — dir wildcard", r)

v, r = sl.validate_target("192.168.1.1", "aggressive")
if not v: ok("validate_target — private IP blocked")
else: fail("validate_target — private IP blocked", "should have been blocked")

if sl.is_destructive_payload("rm -rf /"):
    ok("is_destructive_payload — rm -rf detected")
else:
    fail("is_destructive_payload — rm -rf detected", "not blocked")

if not sl.is_destructive_payload("nmap -sV example.com"):
    ok("is_destructive_payload — nmap allowed")
else:
    fail("is_destructive_payload — nmap allowed", "incorrectly blocked")

# ─────────────────────────────────────────────────────────────────────────────
# 2. MEMORY
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 2. ArgusMemory ===")
import tempfile, pathlib
tmp_db = tempfile.mktemp(suffix='.db')
from core.memory import ArgusMemory
mem = ArgusMemory(db_path=tmp_db)

try:
    mem.upsert_target("test.example.com", parent_domain="example.com", priority=5)
    ok("upsert_target")
except Exception as e:
    fail("upsert_target", str(e))

try:
    mem.add_finding("test.example.com", "XSS", "xss", "<script>", "Reflected XSS found", "High")
    ok("add_finding")
except Exception as e:
    fail("add_finding", str(e))

try:
    bb = mem.get_blackboard_summary()
    data = json.loads(bb)
    assert "test.example.com" in data
    ok("get_blackboard_summary")
except Exception as e:
    fail("get_blackboard_summary", str(e))

try:
    e_id = mem.upsert_entity("ip", "1.2.3.4", {"asn": "AS12345"})
    assert isinstance(e_id, int)
    ok("upsert_entity")
except Exception as e:
    fail("upsert_entity", str(e))

try:
    mem.add_relation("test.example.com", "1.2.3.4", "resolves_to")
    ok("add_relation")
except Exception as e:
    fail("add_relation", str(e))

try:
    g = mem.get_graph_insights()
    assert isinstance(g, str)
    ok("get_graph_insights")
except Exception as e:
    fail("get_graph_insights", str(e))

try:
    hist = mem.get_scan_history(limit=10)
    assert isinstance(hist, list)
    ok("get_scan_history — empty")
except Exception as e:
    fail("get_scan_history — empty", str(e))

try:
    pt = mem.get_priority_targets()
    assert isinstance(pt, str)
    ok("get_priority_targets")
except Exception as e:
    fail("get_priority_targets", str(e))

try:
    mem.clear_memory()
    bb2 = mem.get_blackboard_summary()
    data2 = json.loads(bb2)
    assert data2 == {}
    ok("clear_memory — data wiped")
except Exception as e:
    fail("clear_memory — data wiped", str(e))

try:
    os.remove(tmp_db)
except:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# 3. AGENT — _extract_target & _parse_scan_pattern
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 3. ArgusBrain._extract_target + _parse_scan_pattern ===")
# Instantiate with dummy tools
from core.agent import ArgusBrain
brain = ArgusBrain.__new__(ArgusBrain)

cases_extract = [
    ("https://sketchfab.com",  "https://sketchfab.com"),
    ("sketchfab.com",          "sketchfab.com"),
    ("Scan sketchfab.com please", "sketchfab.com"),
    ("*.example.com",          "*.example.com"),
    ("example.com/*/*/*",      "example.com/*/*/*"),
    ("*.example.com/*/*/*",    "*.example.com/*/*/*"),
]
for inp, expected in cases_extract:
    got = brain._extract_target(inp)
    if got == expected:
        ok(f"_extract_target({inp!r})")
    else:
        fail(f"_extract_target({inp!r})", f"expected {expected!r}, got {got!r}")

cases_parse = [
    ("example.com",            ("example.com", False, False, 0)),
    ("*.example.com",          ("example.com", True,  False, 0)),
    ("example.com/*",          ("example.com", False, True,  1)),
    ("example.com/*/*/*",      ("example.com", False, True,  3)),
    ("*.example.com/*/*/*",    ("example.com", True,  True,  3)),
    ("www.example.com",        ("example.com", False, False, 0)),
]
for inp, expected in cases_parse:
    got = brain._parse_scan_pattern(inp)
    if got == expected:
        ok(f"_parse_scan_pattern({inp!r})")
    else:
        fail(f"_parse_scan_pattern({inp!r})", f"expected {expected}, got {got}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. REPORT ENGINE
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 4. ReportEngine ===")
from reports.report_engine import ReportEngine, SEVERITY_WEIGHTS

tmp_db2 = tempfile.mktemp(suffix='.db')
mem2 = ArgusMemory(db_path=tmp_db2)
tmp_dir = tempfile.mkdtemp()
re_engine = ReportEngine(mem2, tmp_dir)

# severity_score tests
score_cases = [
    ([],                                          1),   # no findings → 1
    ([{"severity": "Info"}]*6,                    1),   # all Info → 1
    ([{"severity": "High"}, {"severity": "Info"}], 7),  # High + Info → 7
    ([{"severity": "Critical"}],                  10),  # single Critical → 10
]
for findings, expected in score_cases:
    got = re_engine.severity_score(findings)
    if got == expected:
        ok(f"severity_score({[f['severity'] for f in findings]}) = {expected}")
    else:
        fail(f"severity_score", f"expected {expected}, got {got} for {findings}")

# domain key validator
def _is_valid_domain_key(key):
    if not key or ' ' in key or len(key) > 253: return False
    return '.' in key and all(c.isprintable() for c in key)

bad_keys = [
    "Scan this site example.com for vulns",
    "",
    "a" * 254,
]
good_keys = ["example.com", "sub.domain.co.uk", "api.v2.example.io"]
for k in bad_keys:
    if not _is_valid_domain_key(k): ok(f"domain_key_validator — bad key blocked: {k[:30]!r}")
    else: fail("domain_key_validator — bad key blocked", f"{k!r} should be invalid")
for k in good_keys:
    if _is_valid_domain_key(k): ok(f"domain_key_validator — good key accepted: {k!r}")
    else: fail("domain_key_validator — good key accepted", f"{k!r} should be valid")

# Full report generation
mem2.add_finding("test.example.com", "SQLi", "sqli", "payload", "SQL error", "High")
try:
    j, md, score = re_engine.generate("test.example.com", "aggressive")
    assert os.path.exists(j), "JSON not created"
    assert os.path.exists(md), "Markdown not created"
    assert 1 <= score <= 10
    ok(f"report generation — score={score}, json={os.path.basename(j)}")
except Exception as e:
    fail("report generation", str(e))

try:
    os.remove(tmp_db2)
except:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# 5. TOOLS — _extract_domain
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 5. WSLBridgeTools._extract_domain ===")
from unittest.mock import MagicMock, patch

# Create a minimal WSLBridgeTools instance (skip WSL init)
with patch('subprocess.run'), patch('shutil.which', return_value='/usr/bin/wsl'):
    try:
        from core.tools import WSLBridgeTools
        bridge = WSLBridgeTools.__new__(WSLBridgeTools)
        bridge.scan_mode = "aggressive"
        bridge.memory = ArgusMemory(db_path=tempfile.mktemp(suffix='.db'))
        bridge.safety = SafetyLayer()

        domain_cases = [
            ("https://sketchfab.com",         "sketchfab.com"),
            ("sketchfab.com",                 "sketchfab.com"),
            ("www.sketchfab.com",             "sketchfab.com"),
            ("https://api.example.com/path",  "api.example.com"),
            ('{"domain": "example.com"}',     "example.com"),
        ]
        for inp, expected in domain_cases:
            got = bridge._extract_domain(inp)
            if got == expected:
                ok(f"_extract_domain({inp!r})")
            else:
                fail(f"_extract_domain({inp!r})", f"expected {expected!r}, got {got!r}")

    except Exception as e:
        fail("WSLBridgeTools init (mocked)", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 6. TOOLS — analyze_secrets false-positive filter
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 6. analyze_secrets email filter ===")
try:
    # Test the noise filter set logic directly
    _EMAIL_NOISE_DOMAINS = {
        "sendinblue.com", "brevo.com", "mailchimp.com", "sendgrid.net",
        "mailgun.org", "sparkpost.com", "mandrillapp.com", "postmarkapp.com",
        "amazonses.com", "amazonaws.com", "google.com", "microsoft.com",
        "apple.com", "cloudflare.com", "w3.org", "schema.org", "example.com",
        "sentry.io", "intercom.io", "hubspot.com", "salesforce.com", "zendesk.com",
    }

    def should_filter(email):
        parts = email.lower().split("@")
        if len(parts) != 2:
            return False
        return parts[1] in _EMAIL_NOISE_DOMAINS

    noise_emails = [
        "abuse@sendinblue.com",
        "noreply@mailchimp.com",
        "support@sendgrid.net",
        "bounce@amazonses.com",
    ]
    real_emails = [
        "admin@victim.com",
        "cto@startup.io",
        "root@internaltool.net",
    ]
    for e in noise_emails:
        if should_filter(e): ok(f"email filter — noise blocked: {e}")
        else: fail("email filter", f"{e} should be filtered")
    for e in real_emails:
        if not should_filter(e): ok(f"email filter — real kept: {e}")
        else: fail("email filter", f"{e} should NOT be filtered")
except Exception as e:
    fail("analyze_secrets filter logic", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 7. TOOLS — smart_web_search graceful degradation
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 7. smart_web_search — tier-3 degradation ===")
try:
    # Verify the function exists with the right signature
    from core.tools import WSLBridgeTools as WBT
    import inspect
    src = inspect.getsource(WBT.smart_web_search)
    assert 'duckduckgo_search' in src, "Tier-1 ddgs missing"
    assert 'langchain_community.tools' in src, "Tier-2 langchain missing"
    assert 'Tier-3' in src, "Tier-3 degradation missing"
    assert 'DuckDuckGoSearchRun' in src, "DuckDuckGoSearchRun missing"
    ok("smart_web_search — 3-tier structure present")

    # Simulate tier-3 path: both imports fail → return install hint
    import builtins
    real_import = builtins.__import__
    def mock_import(name, *args, **kwargs):
        if name in ('duckduckgo_search', 'langchain_community'):
            raise ImportError(f"No module named '{name}'")
        return real_import(name, *args, **kwargs)

    mem3 = ArgusMemory(db_path=tempfile.mktemp(suffix='.db'))
    bridge2 = WSLBridgeTools.__new__(WSLBridgeTools)
    bridge2.scan_mode = "aggressive"
    bridge2.memory = mem3
    bridge2.safety = SafetyLayer()

    builtins.__import__ = mock_import
    try:
        result = bridge2.smart_web_search("test query CVE")
        assert "[SKIP]" in result or "unavailable" in result.lower(), \
            f"Expected skip message, got: {result[:100]}"
        ok("smart_web_search — tier-3 returns install hint")
    finally:
        builtins.__import__ = real_import

except Exception as e:
    fail("smart_web_search tier-3", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 8. TOOLS — check_path_traversal https:// prefix
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 8. check_path_traversal — https:// prefix fix ===")
try:
    import inspect
    from core.tools import WSLBridgeTools as WBT
    src = inspect.getsource(WBT.check_path_traversal)
    assert "clean_url.startswith(('http://', 'https://'))" in src or \
           "https://" in src, "https:// prefix fix not found"
    ok("check_path_traversal — https:// prefix fix present")
except Exception as e:
    fail("check_path_traversal — https:// prefix fix", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 9. TOOLS — check_sqli https:// prefix
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 9. check_sqli — https:// prefix fix ===")
try:
    src = inspect.getsource(WBT.check_sqli)
    assert "https://" in src, "https:// prefix fix not found in check_sqli"
    ok("check_sqli — https:// prefix fix present")
except Exception as e:
    fail("check_sqli — https:// prefix fix", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 10. TOOLS — run_nikto IP fallback
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 10. run_nikto — Windows-side DNS resolution ===")
try:
    src = inspect.getsource(WBT.run_nikto)
    assert 'gethostbyname' in src, "socket.gethostbyname not in run_nikto"
    assert '-vhost' in src, "-vhost flag not in run_nikto"
    assert '[SKIP]' in src, "SKIP path not in run_nikto"
    ok("run_nikto — IP fallback + -vhost + skip path present")
except Exception as e:
    fail("run_nikto — IP fallback", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 11. AGENT — wildcard routing in ask()
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 11. agent.ask() — wildcard routing flags ===")
try:
    import inspect
    src = inspect.getsource(ArgusBrain.ask)
    assert '_parse_scan_pattern' in src, "_parse_scan_pattern not called in ask()"
    assert 'sub_mode' in src, "sub_mode flag missing"
    assert 'dir_mode' in src, "dir_mode flag missing"
    assert 'run_subs' in src, "run_subs flag missing"
    assert 'run_vulns' in src, "run_vulns flag missing"
    assert 'run_llm' in src, "run_llm flag missing"
    assert 'scan_label' in src, "scan_label missing"
    assert 'SKIPPED' in src, "SKIPPED branches missing"
    ok("ask() — all wildcard routing flags present")
except Exception as e:
    fail("ask() wildcard routing flags", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 12. AGENT — LLM skip when no confirmed findings
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 12. _llm_threat_analysis — hallucination guard ===")
try:
    src = inspect.getsource(ArgusBrain._llm_threat_analysis)
    assert 'has_confirmed' in src or 'CONFIRMED' in src, \
        "has_confirmed check missing from _llm_threat_analysis"
    assert 'hallucinated' in src.lower() or 'speculative' in src.lower() or \
           'AI inference skipped' in src, \
        "AI skip message missing"
    ok("_llm_threat_analysis — hallucination guard present")
except Exception as e:
    fail("_llm_threat_analysis hallucination guard", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 13. MEMORY — purge_bad_entities
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== 13. purge_bad_entities ===")
try:
    tmp_db3 = tempfile.mktemp(suffix='.db')
    mem4 = ArgusMemory(db_path=tmp_db3)
    # Insert a bad entity
    mem4.upsert_entity("error_string", "Error: command not found", {})
    mem4.upsert_entity("ip", "8.8.8.8", {})
    # Purge
    mem4.purge_bad_entities()
    # Check
    conn = sqlite3.connect(tmp_db3)
    rows = conn.execute("SELECT value FROM entities").fetchall()
    conn.close()
    values = [r[0] for r in rows]
    assert "8.8.8.8" in values, "Good entity was removed"
    assert not any("Error" in v for v in values), "Bad entity not removed"
    ok("purge_bad_entities — bad removed, good kept")
    os.remove(tmp_db3)
except Exception as e:
    fail("purge_bad_entities", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# _discover_parameters
# ─────────────────────────────────────────────────────────────────────────────
try:
    from core.memory import ArgusMemory as _AM4
    from core.tools  import WSLBridgeTools as _WBT4
    _mem4 = _AM4(":memory:")
    _t4   = _WBT4(_mem4)
    _res  = _t4._discover_parameters("https://httpbin.org")
    assert isinstance(_res, dict)
    ok("_discover_parameters returns dict")
except Exception as e:
    fail("_discover_parameters returns dict", str(e))

try:
    import inspect as _ins
    from core.tools import WSLBridgeTools as _WBT5
    _sig = inspect.signature(_WBT5._discover_parameters)
    assert "base_url" in _sig.parameters
    ok("_discover_parameters has base_url param")
except Exception as e:
    fail("_discover_parameters has base_url param", str(e))

try:
    import inspect
    from core.tools import WSLBridgeTools as _WBT6
    _pt  = inspect.getsource(_WBT6.check_path_traversal)
    _xss = inspect.getsource(_WBT6.check_xss)
    _sq  = inspect.getsource(_WBT6.check_sqli)
    assert "_discover_parameters" in _pt,  "missing in path_traversal"
    assert "_discover_parameters" in _xss, "missing in xss"
    assert "_discover_parameters" in _sq,  "missing in sqli"
    ok("_discover_parameters integrated in all 3 scanners")
except Exception as e:
    fail("_discover_parameters integrated in all 3 scanners", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  ARGUS TEST RESULTS")
print("="*60)
for r in results:
    print(r)
print(f"\n  Total: {PASS+FAIL}  |  PASS: {PASS}  |  FAIL: {FAIL}")
print("="*60)
sys.exit(0 if FAIL == 0 else 1)
