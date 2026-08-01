"""Unit tests for ArgusBrain's deterministic (no-LLM) report builder and the
fast/full scan-profile selection.

The report is built straight from the confirmed findings the pipeline's tools
persist in memory - a weak local model can neither slow it down nor drop a real
finding. `object.__new__` bypasses ArgusBrain's heavy __init__ (LLM/RAG wiring)
since only `.memory` and the pure helper methods are exercised here.
"""
from unittest.mock import MagicMock

from app.core.agent.brain import (
    DETERMINISTIC_PHASES,
    DETERMINISTIC_PHASES_FAST,
    ArgusBrain,
    _selected_deterministic_phases,
)


def _brain_with_findings(findings):
    brain = object.__new__(ArgusBrain)
    brain.memory = MagicMock()
    brain.memory.get_detailed_findings.return_value = findings
    return brain


def test_confirmed_traversal_renders_as_high_severity():
    brain = _brain_with_findings([
        {
            "tool_name": "path_traversal",
            "data_type": "vulnerability",
            "raw_data": "Traversal: https://x/image?filename=../../../etc/passwd",
            "summary": "LFI/Path Traversal Confirmed (/etc/passwd read success)",
        },
    ])

    report = brain._build_deterministic_report("https://x", {"Path_Traversal_Scan": "..."})

    assert report["overall_risk_score"] == 9
    assert len(report["findings"]) == 1
    f = report["findings"][0]
    assert f["severity"] == "High"
    assert "traversal" in f["issue"].lower()
    assert f["suggested_payload"] == "../../../etc/passwd"
    assert f["remediation"]


def test_no_vulnerability_findings_yields_empty_low_risk_report():
    brain = _brain_with_findings([
        {"tool_name": "crawler", "data_type": "link", "raw_data": "/products"},
    ])

    report = brain._build_deterministic_report("https://x", {})

    assert report["findings"] == []
    assert report["overall_risk_score"] == 1
    assert "No vulnerabilities" in report["next_steps"][0] or report["next_steps"]


def test_duplicate_findings_are_deduplicated():
    dup = {
        "tool_name": "path_traversal",
        "data_type": "vulnerability",
        "raw_data": "Traversal: https://x/image?filename=../../../etc/passwd",
        "summary": "LFI/Path Traversal Confirmed (/etc/passwd read success)",
    }
    brain = _brain_with_findings([dup, dict(dup)])

    report = brain._build_deterministic_report("https://x", {})

    assert len(report["findings"]) == 1


def test_sqli_finding_classified_high_with_sql_remediation():
    brain = _brain_with_findings([
        {
            "tool_name": "evasion_probe",
            "data_type": "vulnerability",
            "raw_data": "SQLi: 1 OR 1=1",
            "summary": "SQLi potential via WAF evasion",
        },
    ])

    report = brain._build_deterministic_report("https://x", {})

    assert report["findings"][0]["severity"] == "High"
    assert "parameterized" in report["findings"][0]["remediation"].lower()


def test_recon_and_nikto_noise_is_excluded_from_findings():
    """Nikto/recon store every output line as data_type 'vulnerability'
    (Server banner, ports, 'host tested', connect failures). These are not
    confirmed exploits and must never appear as report findings."""
    brain = _brain_with_findings([
        {"tool_name": "nikto", "data_type": "vulnerability",
         "raw_data": "* Server: nginx", "summary": "Potential vulnerability detected"},
        {"tool_name": "recon", "data_type": "vulnerability",
         "raw_data": "* Target Port: 443", "summary": "Potential vulnerability detected"},
    ])

    report = brain._build_deterministic_report("https://x", {})

    assert report["findings"] == []
    assert report["overall_risk_score"] == 1


def test_report_is_scoped_to_the_current_run_via_since():
    """The persistent blackboard holds findings from prior runs; the report
    must pass the run-start timestamp so only this run's findings are read."""
    brain = _brain_with_findings([])

    brain._build_deterministic_report("https://x", {}, "2026-07-20T10:00:00")

    _, kwargs = brain.memory.get_detailed_findings.call_args
    assert kwargs.get("since") == "2026-07-20T10:00:00"


def test_fast_profile_is_the_default(monkeypatch):
    monkeypatch.delenv("ARGUS_SCAN_PROFILE", raising=False)
    assert _selected_deterministic_phases() == DETERMINISTIC_PHASES_FAST
    assert "Path_Traversal_Scan" in DETERMINISTIC_PHASES_FAST


def test_full_profile_selected_by_env(monkeypatch):
    monkeypatch.setenv("ARGUS_SCAN_PROFILE", "full")
    assert _selected_deterministic_phases() == DETERMINISTIC_PHASES
    assert "Run_Nikto" in DETERMINISTIC_PHASES
