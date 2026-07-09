from app.core.agent.react_prompts import build_react_system_prompt


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
        prompt = build_react_system_prompt(_make_state())
        assert "PHASE 1" in prompt
        assert "PHASE 7" in prompt
        assert "Check_Reachability first, always" in prompt

    def test_includes_thoroughness_rule(self):
        prompt = build_react_system_prompt(_make_state())
        assert "Reconnaissance alone" in prompt
        assert "NOT a complete analysis" in prompt

    def test_includes_risk_score_consistency_rule(self):
        prompt = build_react_system_prompt(_make_state())
        assert "overall_risk_score MUST match" in prompt

    def test_shows_no_calls_yet_when_history_empty(self):
        prompt = build_react_system_prompt(_make_state(tool_call_history=[]))
        assert "(none yet)" in prompt

    def test_shows_prior_calls_in_history_block(self):
        prompt = build_react_system_prompt(
            _make_state(tool_call_history=["Check_Reachability::https://example.com"])
        )
        assert 'Check_Reachability("https://example.com")' in prompt
