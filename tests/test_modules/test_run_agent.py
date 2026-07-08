"""Unit tests for scripts/run_agent.py (specs/017-restore-react-agent).

Covers _build_final_state()'s shaping of ArgusBrain.ask()'s return value -
the seam between the ReAct agent's output and what the GUI's Agent tab
renders. Full subprocess/live-LLM flow is exercised by the Streamlit
AppTest smoke test (manual verification, per specs/017/quickstart.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.run_agent import _build_final_state


def test_build_final_state_with_valid_structured_report():
    result = {
        "output": {
            "summary": "ok", "attack_surface_stats": "1 host",
            "findings": [{"target": "x", "issue": "y", "severity": "Low"}],
            "overall_risk_score": 4, "next_steps": ["step1"], "output": "full report",
        }
    }

    final_state = _build_final_state(result, "production", "https://example.com")

    assert final_state["overall_risk_score"] == 4
    assert final_state["findings"] == [{"target": "x", "issue": "y", "severity": "Low"}]
    assert final_state["output"] == "full report"
    assert "parse_warning" not in final_state
    assert final_state["mode"] == "production"
    assert final_state["target"] == "https://example.com"


def test_build_final_state_with_unparsed_raw_string_flags_a_warning_not_a_fabricated_report():
    result = {"output": "the LLM just rambled, no JSON here"}

    final_state = _build_final_state(result, "production", "https://example.com")

    assert final_state["overall_risk_score"] is None
    assert final_state["findings"] == []
    assert "parse_warning" in final_state
    assert final_state["output"] == "the LLM just rambled, no JSON here"


def test_build_final_state_with_error_dict_flags_a_warning():
    result = {"output": {"error": "executor_unavailable", "message": "boom"}}

    final_state = _build_final_state(result, "production", "https://example.com")

    assert final_state["overall_risk_score"] is None
    assert "parse_warning" in final_state


def test_build_final_state_with_non_dict_result_does_not_raise():
    final_state = _build_final_state(None, "production", "https://example.com")

    assert final_state["overall_risk_score"] is None
    assert "parse_warning" in final_state
