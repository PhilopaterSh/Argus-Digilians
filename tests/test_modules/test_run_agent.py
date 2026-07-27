"""Unit tests for scripts/run_agent.py (specs/017-restore-react-agent).

Covers _build_final_state()'s shaping of ArgusBrain.ask()'s return value -
the seam between the ReAct agent's output and what the GUI's Agent tab
renders. Full subprocess/live-LLM flow is exercised by the Streamlit
AppTest smoke test (manual verification, per specs/017/quickstart.md).
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import scripts.run_agent as run_agent_module
from scripts.run_agent import _build_final_state

pytestmark = pytest.mark.unit


def test_build_final_state_with_valid_structured_report():
    """Verify Build final state with valid structured report."""
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
    """Verify Build final state with unparsed raw string flags a warning not a fabricated report."""
    result = {"output": "the LLM just rambled, no JSON here"}

    final_state = _build_final_state(result, "production", "https://example.com")

    assert final_state["overall_risk_score"] is None
    assert final_state["findings"] == []
    assert "parse_warning" in final_state
    assert final_state["output"] == "the LLM just rambled, no JSON here"


def test_build_final_state_with_error_dict_flags_a_warning():
    """Verify Build final state with error dict flags a warning."""
    result = {"output": {"error": "executor_unavailable", "message": "boom"}}

    final_state = _build_final_state(result, "production", "https://example.com")

    assert final_state["overall_risk_score"] is None
    assert "parse_warning" in final_state


def test_build_final_state_with_non_dict_result_does_not_raise():
    """Verify Build final state with non dict result does not raise."""
    final_state = _build_final_state(None, "production", "https://example.com")

    assert final_state["overall_risk_score"] is None
    assert "parse_warning" in final_state


def _fake_run_brain_analysis(target, run_id, mode, state_file, result_box):
    """Fake run brain analysis."""
    result_box["result"] = {"output": {"summary": "ok", "findings": [], "overall_risk_score": 1, "next_steps": [], "output": "done"}}


class TestRunIdPassthrough:
    """Regression test: AgentController.start() generates a run_id to name the
    state file itself, then spawned this process without telling it that
    run_id - main() silently generated a SECOND, different run_id and
    overwrote the state file's own run_id field with it, so the file's name
    and its content disagreed about which run it was. --run-id closes that
    gap; main() must use it verbatim, not generate its own."""

    def test_main_uses_the_provided_run_id_verbatim(self, tmp_path):
        """Verify Main uses the provided run id verbatim.
        
        Args:
            tmp_path: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        state_file = tmp_path / "agent_test.json"
        with patch.object(run_agent_module, "run_brain_analysis", _fake_run_brain_analysis), \
             patch.object(sys, "argv", [
                 "run_agent.py",
                 "--target", "https://example.com",
                 "--state-file", str(state_file),
                 "--run-id", "caller-issued-run-id",
             ]):
            run_agent_module.main()

        written = json.loads(state_file.read_text(encoding="utf-8"))
        assert written["run_id"] == "caller-issued-run-id"

    def test_main_falls_back_to_a_generated_run_id_when_not_provided(self, tmp_path):
        """Verify Main falls back to a generated run id when not provided.
        
        Args:
            tmp_path: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
        """
        state_file = tmp_path / "agent_test.json"
        with patch.object(run_agent_module, "run_brain_analysis", _fake_run_brain_analysis), \
             patch.object(sys, "argv", [
                 "run_agent.py",
                 "--target", "https://example.com",
                 "--state-file", str(state_file),
             ]):
            run_agent_module.main()

        written = json.loads(state_file.read_text(encoding="utf-8"))
        assert written["run_id"]
        assert written["run_id"] != "caller-issued-run-id"
