"""Unit tests for the consolidated ArgusBrain (app.core.agent.brain).

Covers the tool-dispatch surface that used to live on the deprecated
ArgusBrainV2 (app.core.agent.brain_v2, removed per specs/012 T026).
"""
import pytest
from langchain_core.tools import Tool

from app.core.agent.brain import ArgusBrain

pytestmark = pytest.mark.unit


def _make_brain():
    """Build an ArgusBrain with one fake tool and RAG disabled, for tool-dispatch tests.

    Returns:
        ArgusBrain: Configured with a single "fake" tool.
    """
    def fake_func(x: str = "") -> str:
        """Fake func."""
        return f"executed:{x}"

    tool = Tool(name="fake", description="A fake tool", func=fake_func)
    return ArgusBrain("test-model", [tool], rag_config={"enabled": False})


def test_dispatch_calls_tool_func():
    """Verify Dispatch calls tool func."""
    brain = _make_brain()
    result = brain.dispatch("fake", x="hello")
    assert result == "executed:hello"


def test_dispatch_unknown_tool_raises():
    """Verify Dispatch unknown tool raises."""
    brain = _make_brain()
    with pytest.raises(KeyError, match="Tool not found: unknown"):
        brain.dispatch("unknown")


def test_get_available_tools():
    """Verify Get available tools."""
    brain = _make_brain()
    tools = brain.get_available_tools()
    assert len(tools) == 1
    assert tools[0].name == "fake"


def test_get_tool_names():
    """Verify Get tool names."""
    brain = _make_brain()
    assert brain.get_tool_names() == ["fake"]


def test_no_tools_on_init():
    """Verify No tools on init."""
    brain = ArgusBrain("test-model", [], rag_config={"enabled": False})
    assert brain.get_tool_names() == []


class TestBlackboardReconciliation:
    """Live failure 2026-07-27, PortSwigger lab: `Path_Traversal_Scan`
    confirmed `/image?filename=....//....//....//etc/passwd` with a real
    `root:x:0:0:` read and recorded it to the Blackboard, but the delivered
    report carried `suggested_payload: ""`, `tool_source: null` and the bare
    site root as its target - so the UI showed "Suggested payload: n/a" and
    the one piece of reproducible proof was lost. An earlier run on the same
    class dropped the finding entirely.

    `SecurityReport.findings` is authored free-hand by the model and copied
    verbatim by `run_agent._build_final_state`; these tests pin the repair
    pass that restores what a tool actually recorded.
    """

    TARGET = "https://0a6700e3.web-security-academy.net/"
    RECORDED = (
        "Traversal: https://0a6700e3.web-security-academy.net/image"
        "?filename=....//....//....//etc/passwd"
    )

    @staticmethod
    def _brain_with_findings(rows):
        """Build a brain whose Blackboard returns `rows`.

        Args:
            rows (list[dict]): Finding dicts to return from
                `get_detailed_findings`.

        Returns:
            ArgusBrain: Wired to a stub memory.
        """
        class _Memory:
            def get_detailed_findings(self, domain, since=None):
                """Return the canned rows regardless of domain."""
                return rows

        brain = ArgusBrain("test-model", [], rag_config={"enabled": False})
        brain.memory = _Memory()
        return brain

    def _traversal_row(self):
        """Build a blackboard row shaped like a recorded path-traversal finding."""
        return {
            "tool_name": "path_traversal",
            "data_type": "vulnerability",
            "raw_data": self.RECORDED,
            "summary": "LFI/Path Traversal Confirmed (/etc/passwd read success)",
            "severity": "High",
        }

    def test_backfills_the_payload_the_model_dropped(self):
        """Reconciliation backfills concrete payload evidence the report prose omitted."""
        brain = self._brain_with_findings([self._traversal_row()])
        result = {"output": {"findings": [{
            "target": self.TARGET,
            "issue": "Path Traversal",
            "severity": "High",
            "description": "The target has a confirmed path traversal vulnerability.",
            "suggested_payload": "",
            "remediation": "",
        }]}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        finding = result["output"]["findings"][0]
        assert finding["suggested_payload"] == "....//....//....//etc/passwd"
        assert finding["tool_source"] == "path_traversal"
        assert finding["target"].endswith("/image")
        assert "filename" in finding["description"]

    def test_recovers_a_finding_the_model_omitted_entirely(self):
        """The 'Findings Count: 0 despite a confirmed hit' case."""
        brain = self._brain_with_findings([self._traversal_row()])
        result = {"output": {"findings": []}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        findings = result["output"]["findings"]
        assert len(findings) == 1
        assert findings[0]["suggested_payload"] == "....//....//....//etc/passwd"
        assert findings[0]["tool_source"] == "path_traversal"
        assert findings[0]["target"].endswith("/image")

    def test_does_not_duplicate_a_finding_already_reported(self):
        """A blackboard finding already reflected in the report is not appended twice."""
        brain = self._brain_with_findings([self._traversal_row()])
        result = {"output": {"findings": [{
            "target": "https://0a6700e3.web-security-academy.net/image",
            "issue": "Path Traversal",
            "severity": "High",
            "description": "Confirmed via the filename parameter.",
            "suggested_payload": "....//....//....//etc/passwd",
            "remediation": "Validate input.",
            "tool_source": "path_traversal",
        }]}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        assert len(result["output"]["findings"]) == 1

    def test_never_overwrites_a_value_the_model_supplied(self):
        """Model-supplied field values win; reconciliation only fills gaps."""
        brain = self._brain_with_findings([self._traversal_row()])
        result = {"output": {"findings": [{
            "target": "https://0a6700e3.web-security-academy.net/image",
            "issue": "Path Traversal",
            "severity": "High",
            "description": "Confirmed via the filename parameter.",
            "suggested_payload": "../../../etc/passwd",
            "remediation": "Validate input.",
            "tool_source": "manual",
        }]}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        finding = result["output"]["findings"][0]
        assert finding["suggested_payload"] == "../../../etc/passwd"
        assert finding["tool_source"] == "manual"

    def test_noop_without_memory(self):
        """With brain.memory unset, reconciliation is a harmless no-op."""
        brain = ArgusBrain("test-model", [], rag_config={"enabled": False})
        brain.memory = None
        result = {"output": {"findings": []}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        assert result["output"]["findings"] == []

    def test_noop_when_nothing_was_confirmed(self):
        """A clean scan must stay clean - no fabricated findings."""
        brain = self._brain_with_findings([
            {"tool_name": "crawler", "data_type": "link",
             "raw_data": "http://x/y?z=1", "summary": "", "severity": "Info"},
        ])
        result = {"output": {"findings": []}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        assert result["output"]["findings"] == []

    def test_error_output_is_left_alone(self):
        """Error-shaped results bypass reconciliation completely."""
        brain = self._brain_with_findings([self._traversal_row()])
        result = {"output": {"error": "no_final_answer", "message": "..."}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        assert result["output"] == {"error": "no_final_answer", "message": "..."}

    def test_blackboard_read_failure_is_swallowed(self):
        """A raising memory backend degrades to a no-op instead of failing the run."""
        class _Broken:
            def get_detailed_findings(self, domain, since=None):
                """Raise, as a corrupt/locked DB would."""
                raise RuntimeError("db locked")

        brain = ArgusBrain("test-model", [], rag_config={"enabled": False})
        brain.memory = _Broken()
        result = {"output": {"findings": []}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        assert result["output"]["findings"] == []

    def test_parses_evasion_style_rows_without_an_endpoint(self):
        """evasion.py records `Traversal: <payload>` with no URL."""
        brain = self._brain_with_findings([{
            "tool_name": "evasion_probe", "data_type": "vulnerability",
            "raw_data": "SQLi: 1'/**/OR/**/1=1/**/--",
            "summary": "SQLi potential via WAF evasion", "severity": "High",
        }])
        result = {"output": {"findings": []}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        finding = result["output"]["findings"][0]
        assert finding["suggested_payload"] == "1'/**/OR/**/1=1/**/--"
        assert finding["issue"] == "SQLi"
        assert finding["target"] == self.TARGET

    def test_high_severity_vulnerability_rows_are_also_reconciled(self):
        """reflective_verification.py uses data_type
        'high_severity_vulnerability', which must not be missed."""
        brain = self._brain_with_findings([{
            "tool_name": "reflective_verification",
            "data_type": "high_severity_vulnerability",
            "raw_data": "Traversal: https://x/image?filename=../../etc/passwd",
            "summary": "VERIFIED: /etc/passwd read", "severity": "Critical",
        }])
        result = {"output": {"findings": []}}

        brain._reconcile_findings_with_blackboard(result, self.TARGET)

        assert len(result["output"]["findings"]) == 1
        assert result["output"]["findings"][0]["severity"] == "Critical"
