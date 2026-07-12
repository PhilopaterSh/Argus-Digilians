"""
Argus RAG Knowledge Base — local vulnerability intelligence for LLM-guided reasoning.
Maps detected tech stacks to CVEs, attack patterns, and timeout analysis rules.
No external calls — purely local JSON-style structures.
"""

# ── CVE / vuln catalogue per technology ───────────────────────────────────────
TECH_VULNS = {
    "IIS 8.5": [
        {
            "id": "CVE-2015-1635",
            "severity": "Critical",
            "desc": (
                "HTTP.sys RCE via malformed Range header (MS15-034). "
                "Affects IIS 7.5-8.5 on Windows Server 2008-2012 R2."
            ),
            "test_hint": "GET / with header: Range: bytes=0-18446744073709551615",
        },
        {
            "id": "CVE-2017-7269",
            "severity": "Critical",
            "desc": "Buffer overflow in IIS WebDAV PROPFIND handler.",
            "test_hint": "OPTIONS / — check Allow header for PROPFIND, PUT, DELETE",
        },
        {
            "id": "IIS_TILDE_ENUM",
            "severity": "Medium",
            "desc": "IIS 8.3 short filename disclosure via HTTP tilde enumeration.",
            "test_hint": "GET /a~1.asp — different status than random path confirms enumeration",
        },
    ],
    "ASP.NET": [
        {
            "id": "ASP_VIEWSTATE_RCE",
            "severity": "High",
            "desc": (
                "ASP.NET ViewState deserialization RCE when MAC validation disabled "
                "or machineKey leaked. Tool: ysoserial.net."
            ),
            "test_hint": "Find __VIEWSTATE in page source; try altering it — 500 = MAC enabled",
        },
        {
            "id": "ASP_PADDING_ORACLE",
            "severity": "High",
            "desc": "MS10-070 Padding Oracle on ASP.NET encrypted cookies/ViewState.",
            "test_hint": "Use padbuster on encrypted cookies — observe 500 vs 200 differences",
        },
        {
            "id": "ASP_TRACE_AXD",
            "severity": "Medium",
            "desc": "trace.axd / elmah.axd expose request details, stack traces, session data.",
            "test_hint": "GET /trace.axd, /elmah.axd, /Elmah.axd",
        },
        {
            "id": "ASP_SQLI_MSSQL",
            "severity": "Critical",
            "desc": (
                "ASP.NET apps typically use SQL Server. MSSQL errors confirm injection: "
                "'Unclosed quotation mark', 'Microsoft OLE DB Provider for SQL Server'."
            ),
            "test_hint": "Inject ' into all parameters and look for MSSQL error strings",
        },
    ],
    "Microsoft-IIS": [
        {
            "id": "IIS_REQFILTER_BYPASS",
            "severity": "High",
            "desc": (
                "IIS Request Filtering blocks ../ by default but double-URL-encoding "
                "(%252F) or Unicode normalization (%c0%af) may bypass it."
            ),
            "test_hint": "Try: ..%252F..%252F, ..%c0%af..%c0%af, ....//....//",
        },
        {
            "id": "IIS_VERB_TAMPERING",
            "severity": "Medium",
            "desc": "IIS may allow HTTP verbs (PUT, DELETE, TRACE) unrestricted.",
            "test_hint": "OPTIONS / — check Allow header",
        },
    ],
}

PATTERN_RULES = {
    "all_timeouts_baseline_ok": {
        "confidence": "High",
        "label": "WAF/IIS Request Filtering — traversal payloads intercepted",
        "analysis": (
            "ALL path traversal probes timed out while baseline responded normally (<2s). "
            "This strongly indicates IIS Request Filtering or a WAF dropping connections "
            "on '../' sequences. The vulnerability may still exist behind the filter — "
            "next step: attempt encoding bypasses to circumvent the filter."
        ),
        "bypass_payloads": [
            "..%252F..%252FWindows%252Fsystem.ini",
            "..%c0%af..%c0%afWindows/system.ini",
            "....//....//Windows/system.ini",
            ".%2e/.%2e/Windows/system.ini",
            "%2e%2e%2f%2e%2e%2fWindows%2fsystem.ini",
            "..%5C..%5CWindows\\system.ini",
        ],
    },
    "partial_timeouts": {
        "confidence": "Medium",
        "label": "Inconsistent filtering — some payloads blocked, others passed",
        "analysis": (
            "Some traversal probes timed out, others received responses. "
            "Suggests regex-based filtering or rate limiting."
        ),
        "bypass_payloads": [
            "..%252F..%252FWindows%252Fsystem.ini",
            "....//....//Windows/system.ini",
        ],
    },
    "no_timeouts": {
        "confidence": "Low",
        "label": "No filtering detected",
        "analysis": "Server responded to all traversal probes — no connection-drop filter detected.",
        "bypass_payloads": [],
    },
}

ATTACK_HINTS = {
    "ASP.NET": [
        "Inject ' into ALL integer/string parameters — MSSQL errors confirm SQLi",
        "Check page source for __VIEWSTATE — alter it and look for 500 (MAC validation on)",
        "Probe: /trace.axd, /elmah.axd, /Elmah.axd for diagnostic info",
        "Fuzz hidden form inputs and RetURL / redirect parameters",
        "Trigger 500 errors deliberately — ASP.NET default pages leak stack traces",
    ],
    "IIS": [
        "OPTIONS / — enumerate HTTP methods (PUT/DELETE = critical finding)",
        "IIS tilde short name: GET /a~1.asp vs /rand9x.asp — status difference = vulnerable",
        "HTTP.sys CVE-2015-1635: Range: bytes=0-18446744073709551615",
        "Double-encoded traversal: ..%252F..%252F",
        "Check .asa, .cer, .cdx extension handling",
    ],
    "Microsoft": [
        "X-Powered-By header reveals exact ASP.NET version — map to known CVEs",
        "Test OPTIONS on all discovered endpoints",
    ],
}


def get_tech_context(tech_string: str) -> dict:
    """Return relevant CVEs and attack hints for a detected technology string."""
    ts = tech_string.lower()
    result = {"cves": [], "hints": []}
    for tech_key, cves in TECH_VULNS.items():
        if tech_key.lower() in ts:
            result["cves"].extend(cves)
    for tech_key, hints in ATTACK_HINTS.items():
        if tech_key.lower() in ts:
            result["hints"].extend(hints)
    # De-duplicate by CVE id
    seen = set()
    deduped = []
    for c in result["cves"]:
        if c["id"] not in seen:
            seen.add(c["id"])
            deduped.append(c)
    result["cves"] = deduped
    result["hints"] = list(dict.fromkeys(result["hints"]))
    return result


def analyze_timeout_pattern(timeout_count: int, total_probes: int, baseline_ok: bool) -> dict:
    """Classify the path traversal timeout pattern and return analysis + bypass payloads."""
    if total_probes == 0:
        return PATTERN_RULES["no_timeouts"]
    ratio = timeout_count / total_probes
    if ratio >= 0.85 and baseline_ok:
        return PATTERN_RULES["all_timeouts_baseline_ok"]
    if ratio >= 0.4:
        return PATTERN_RULES["partial_timeouts"]
    return PATTERN_RULES["no_timeouts"]


# ─────────────────────────────────────────────────────────────────────────────
# REAL RAG — semantic retrieval over the 1,040 labeled Argus test scenarios
# (knowledge_base/argus_1000_scenarios.json). This is genuine vector search
# (sentence-transformers embeddings + FAISS cosine similarity), not a dict
# lookup. TECH_VULNS/PATTERN_RULES above remain as a zero-dependency, instant
# offline fallback for IIS/ASP.NET — this module now covers everything else
# the 1,040 scenarios span (Next.js, Node/Express, Classic ASP, and more),
# updatable just by replacing the JSON file, no code changes required.
# ─────────────────────────────────────────────────────────────────────────────
import json as _json
from pathlib import Path as _Path

_KB_DIR = _Path(__file__).parent.parent / "knowledge_base"
_SCENARIOS_PATH = _KB_DIR / "argus_1000_scenarios.json"
_INDEX_DIR = _KB_DIR / ".scenario_index"
_INDEX_PATH = _INDEX_DIR / "index.faiss"
_META_PATH = _INDEX_DIR / "meta.json"
_EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # small (~80MB), fast, 384-dim, CPU-friendly

_scenario_state = {"model": None, "index": None, "meta": None, "unavailable": False}


def _load_scenario_engine():
    """Lazily load (or build once, then cache to disk) the FAISS index over
    the labeled scenario dataset. Returns (model, index, meta), or
    (None, None, None) if the dataset or faiss/sentence-transformers aren't
    available. NEVER raises — callers must treat that as 'no RAG this run',
    not a fatal error (the deterministic scanners keep working regardless)."""
    if _scenario_state["unavailable"]:
        return None, None, None
    if _scenario_state["index"] is not None:
        return _scenario_state["model"], _scenario_state["index"], _scenario_state["meta"]

    if not _SCENARIOS_PATH.exists():
        _scenario_state["unavailable"] = True
        return None, None, None

    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        _scenario_state["unavailable"] = True
        return None, None, None

    try:
        with open(_SCENARIOS_PATH, encoding="utf-8") as f:
            scenarios = _json.load(f)

        model = SentenceTransformer(_EMBED_MODEL_NAME)
        index = None

        # Reuse a cached index if it matches the current dataset size exactly.
        if _INDEX_PATH.exists() and _META_PATH.exists():
            try:
                cached_index = faiss.read_index(str(_INDEX_PATH))
                cached_meta = _json.loads(_META_PATH.read_text(encoding="utf-8"))
                if len(cached_meta) == len(scenarios) == cached_index.ntotal:
                    index, scenarios = cached_index, cached_meta
            except Exception:
                index = None  # fall through and rebuild

        if index is None:
            # Embed "target + vulnerability" — the archetype description an
            # analyst would actually match a new target against.
            texts = [f"{s.get('target', '')} {s.get('vulnerability', '')}" for s in scenarios]
            embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
            dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)  # cosine similarity via normalized inner product
            index.add(embeddings.astype("float32"))
            _INDEX_DIR.mkdir(exist_ok=True)
            faiss.write_index(index, str(_INDEX_PATH))
            _META_PATH.write_text(_json.dumps(scenarios, ensure_ascii=False), encoding="utf-8")

        _scenario_state.update(model=model, index=index, meta=scenarios)
        return model, index, scenarios
    except Exception as e:
        print(f"[!] RAG scenario index unavailable: {e}")
        _scenario_state["unavailable"] = True
        return None, None, None


def retrieve_scenario_context(query: str, k: int = 3) -> list:
    """Semantic search over the 1,040 labeled Argus test scenarios.

    `query` is normally a detected tech/target description (e.g. Recon_Suite's
    fingerprint, or the raw target string/purpose). Returns up to `k` scenario
    dicts (id, category, target, vulnerability, argus_behavior, agent_note,
    _similarity), most-similar first. Returns [] if the index or its
    dependencies (faiss-cpu, sentence-transformers) are unavailable — this is
    a best-effort retrieval layer, never a hard failure for the scan."""
    query = (query or "").strip()
    if not query:
        return []
    model, index, meta = _load_scenario_engine()
    if model is None or index is None:
        return []
    try:
        qvec = model.encode([query], normalize_embeddings=True).astype("float32")
        k = max(1, min(k, len(meta)))
        scores, idxs = index.search(qvec, k)
        out = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0 or idx >= len(meta):
                continue
            item = dict(meta[idx])
            item["_similarity"] = round(float(score), 3)
            out.append(item)
        return out
    except Exception as e:
        print(f"[!] RAG scenario retrieval failed: {e}")
        return []
