from app.core.agent.react_prompts import (
    build_collector_prompt,
    build_exploiter_prompt,
    build_planner_prompt,
    build_react_system_prompt,
    build_summarizer_prompt,
)


def _make_state(**overrides):
    state = {
        "target": "https://example.com",
        "phase": "init",
        "iteration_count": 0,
        "max_iterations": 10,
        "blackboard_summary": "No findings yet.",
        "tool_result": None,
        "tool_error": None,
        "tool_call_history": [],
        "_tools": {"Check_Reachability": lambda x: x, "Run_Nikto": lambda x: x},
    }
    state.update(overrides)
    return state


class TestBuildReactSystemPrompt:
    def test_includes_phase_progression_guidance(self):
        """Verify Includes phase progression guidance."""
        prompt = build_react_system_prompt(_make_state())
        assert "PHASE 1" in prompt
        assert "PHASE 8" in prompt
        assert "Check_Reachability first, always" in prompt

    def test_includes_chaining_and_escalation_phase(self):
        """2026-07-10: PHASE 7 restores the old app/core/prompts.py template's
        'Chaining & Escalation' depth using only tools that actually exist on
        WSLBridgeTools today (no Run_Specialized_Module, which was dropped)."""
        prompt = build_react_system_prompt(_make_state())
        assert "PHASE 7 (Chaining & Escalation)" in prompt
        assert "Run_Kali_Command" in prompt

    def test_phase_progression_references_all_5_tools_added_in_chk090(self):
        """specs/018 CHK090: Crawl_Target, Secret_Scanner, Advanced_Evasion_Probe,
        Reflective_Pre_Verify, and Task_Difficulty_Assessment were real, working
        WSLBridgeTools capabilities the agent had no way to invoke - wired into
        brain_tools.py's tool list, so the phase guidance must actually mention
        them or the model has no reason to ever pick them."""
        prompt = build_react_system_prompt(_make_state())
        for tool_name in [
            "Crawl_Target", "Secret_Scanner", "Advanced_Evasion_Probe",
            "Reflective_Pre_Verify", "Task_Difficulty_Assessment",
        ]:
            assert tool_name in prompt, f"{tool_name} not mentioned in phase guidance"

    def test_includes_thoroughness_rule(self):
        """Verify Includes thoroughness rule."""
        prompt = build_react_system_prompt(_make_state())
        assert "Reconnaissance alone" in prompt
        assert "NOT a complete analysis" in prompt

    def test_includes_risk_score_consistency_rule(self):
        """Verify Includes risk score consistency rule."""
        prompt = build_react_system_prompt(_make_state())
        assert "overall_risk_score MUST match" in prompt

    def test_shows_no_calls_yet_when_history_empty(self):
        """Verify Shows no calls yet when history empty."""
        prompt = build_react_system_prompt(_make_state(tool_call_history=[]))
        assert "(none yet)" in prompt

    def test_shows_prior_calls_in_history_block(self):
        """Verify Shows prior calls in history block."""
        prompt = build_react_system_prompt(
            _make_state(tool_call_history=["Check_Reachability::https://example.com"])
        )
        assert 'Check_Reachability("https://example.com")' in prompt


class TestRolePrompts:
    """specs/020 (multi-agent role separation, feature-flagged off by
    default) role-scoped prompt builders."""

    def test_collector_prompt_scopes_to_recon_only(self):
        """Verify Collector prompt scopes to recon only."""
        prompt = build_collector_prompt(_make_state())
        assert "Collector agent" in prompt
        assert "reconnaissance and discovery" in prompt
        assert "Check_Reachability" in prompt

    def test_exploiter_prompt_scopes_to_exploitation_only(self):
        """Verify Exploiter prompt scopes to exploitation only."""
        prompt = build_exploiter_prompt(_make_state())
        assert "Exploiter agent" in prompt
        assert "Run_Nikto" in prompt

    def test_planner_prompt_lists_the_three_specialists(self):
        """Verify Planner prompt lists the three specialists."""
        prompt = build_planner_prompt(_make_state())
        assert "collector:" in prompt
        assert "exploiter:" in prompt
        assert "summarizer:" in prompt

    def test_planner_prompt_shows_role_history(self):
        """Verify Planner prompt shows role history."""
        prompt = build_planner_prompt(_make_state(role_history=["collector", "exploiter"]))
        assert "collector -> exploiter" in prompt

    def test_summarizer_prompt_includes_risk_score_rule(self):
        """Verify Summarizer prompt includes risk score rule."""
        prompt = build_summarizer_prompt(_make_state())
        assert "overall_risk_score MUST match" in prompt
        assert "Final Answer:" in prompt
