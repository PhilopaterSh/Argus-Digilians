"""Unit tests for Argus LangGraph workflow.

Tests both the prebuilt mode (create_react_agent) and custom mode
(text-based ReAct) using mocked LLMs and tools.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from typing import Any
from langchain_core.messages import AIMessage, HumanMessage
from app.core.agent.react_workflow import (
    _ArgusAction,
    _build_custom_workflow,
    _build_prebuilt_workflow,
    _build_reflection_note,
    _build_tool_map,
    _check_early_termination,
    _inter_reflect,
    _supports_tool_calls,
    _try_structured_action,
    _try_structured_final_answer,
    extract_target,
)
from app.core.agent.react_state import ArgusAgentState


# -- Mock helpers -------------------------------------
class MockLLM:
    """A mock LLM that returns predetermined ReAct-format responses."""
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0

    def invoke(self, messages, **kwargs):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return AIMessage(content=response)


def mock_scan(target: str) -> str:
    """Scan target for open ports."""
    return "Open ports: 80, 443. Server: nginx/1.24."


def mock_search(query: str) -> str:
    """Search for CVEs."""
    return "CVE-2024-1234: RCE in nginx."


def mock_recon(target: str) -> str:
    """Reconnaissance scan."""
    return "Subdomains: admin.test.com, api.test.com."


class StructuredMockLLM:
    """Mock LLM simulating Ollama format=json structured decoding (012 FR-C9)."""
    def __init__(self, structured_response=None, raise_on_structured=False):
        self._structured_response = structured_response
        self._raise = raise_on_structured

    def with_structured_output(self, schema):
        if self._raise:
            raise RuntimeError("model does not support format=json")
        response = self._structured_response

        class _Bound:
            def invoke(self, messages):
                """Invoke."""
                return response

        return _Bound()

    def invoke(self, messages, **kwargs):
        """Invoke."""
        return AIMessage(content="Thought: fallback path used.\nFinal Answer: fallback report")


class ReflectionAwareMockLLM:
    """Mock LLM for specs/019 tests: answers ordinary ReAct action-generation
    calls from `react_responses` (cycled, like MockLLM), but answers
    `_inter_reflect`'s fixed yes/no majority-vote prompt from a separate
    `vote_responses` script - distinguished by the prompt's own marker text
    ("Did this tool call achieve"), so a test can control both independently
    without needing two separate LLM instances."""
    def __init__(self, react_responses: list[str], vote_responses: list[str] = None):
        self.react_responses = react_responses
        self.vote_responses = vote_responses or []
        self.react_call_count = 0
        self.vote_call_count = 0

    def invoke(self, messages, **kwargs):
        content = str(messages[-1].content) if messages else ""
        if "Did this tool call achieve" in content:
            resp = self.vote_responses[self.vote_call_count % len(self.vote_responses)]
            self.vote_call_count += 1
            return AIMessage(content=resp)
        resp = self.react_responses[self.react_call_count % len(self.react_responses)]
        self.react_call_count += 1
        return AIMessage(content=resp)


def mock_probe(target: str) -> str:
    """A probe that gets blocked - used to test response-aware reflection notes."""
    return "403 Forbidden - blocked"


def Run_Nikto(target: str) -> str:
    """Stands in for the real Run_Nikto tool - same name, so it's recognised
    by react_workflow.py's EXPLOITATION_TOOLS allowlist for Inter-reflection."""
    return "Nikto scan complete: found /admin/ directory listing enabled."


def mock_flag_tool(target: str) -> str:
    """Returns a flag-shaped string - used to test early-termination detection."""
    return "Retrieved file contents: flag{argus_test_flag_123}"


# -- State fixtures -----------------------------------
BASE_STATE = {
    "messages": [HumanMessage(content="Scan https://test.com")],
    "target": "https://test.com",
    "phase": "recon",
    "blackboard_summary": "",
    "iteration_count": 0,
    "max_iterations": 10,
    "tool_name": None,
    "tool_input": None,
    "tool_result": None,
    "tool_error": None,
    "tool_call_history": [],
    "remaining_steps": 10,
}


# =======================================================
# Tests
# =======================================================

def test_tool_map_building():
    """Verify _build_tool_map converts tool list to name -> func dict."""
    tools = [mock_scan, mock_search]
    tmap = _build_tool_map(tools)
    assert "mock_scan" in tmap, "mock_scan not in tool map"
    assert "mock_search" in tmap, "mock_search not in tool map"
    assert callable(tmap["mock_scan"]), "tool value not callable"
    assert tmap["mock_scan"]("test") == mock_scan("test"), "wrong function mapped"
    print("  [PASS] test_tool_map_building")


def test_target_extraction():
    """Verify extract_target picks URLs and domains from queries."""
    assert extract_target("scan https://example.com") == "https://example.com"
    assert extract_target("Check example.com for vulns") == "example.com"
    assert extract_target("just a query") == "just a query"
    print("  [PASS] test_target_extraction")


def test_custom_graph_full_cycle():
    """Verify custom ReAct graph runs a complete scan->search->report cycle.

    Neither mock_scan nor mock_search is a Phase 5/6 tool, so the first
    "Final Answer" gets the specs/019 phase5/6 nudge once (4th mock response
    absorbs it) before the second Final Answer is accepted."""
    llm = MockLLM([
        "Thought: Scan first.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Now search CVEs.\nAction: mock_search\nAction Input: nginx",
        "Thought: Done.\nFinal Answer: Security report here.",
        "Thought: Understood, no further scanning applies.\nFinal Answer: Security report here (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan, mock_search])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 4, f"Expected 4, got {result['iteration_count']}"
    assert len(result["messages"]) == 8, f"Expected 8 messages, got {len(result['messages'])}"

    last = result["messages"][-1]
    assert "Final Answer:" in last.content, "Last message should contain Final Answer"
    assert result["phase"] == "done", "Phase should be 'done'"
    print("  [PASS] test_custom_graph_full_cycle")


def test_custom_graph_stops_at_max_iterations():
    """Verify custom graph stops when max_iterations is reached."""
    # LLM keeps calling tools indefinitely
    llm = MockLLM([
        "Thought: Keep scanning.\nAction: mock_scan\nAction Input: test",
    ])

    state = dict(BASE_STATE)
    state["max_iterations"] = 2

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(state)

    assert result["iteration_count"] <= state["max_iterations"], \
        f"iteration_count {result['iteration_count']} exceeded max {state['max_iterations']}"
    print(f"  [PASS] test_custom_graph_stops_at_max_iterations (stopped at {result['iteration_count']})")


def test_custom_graph_allows_one_retry_before_blocking_third_identical_call():
    """Regression test: a live run against scanme.nmap.org called Recon_Suite
    with the exact same input 4 times in a row despite it succeeding the
    first time - react_prompts.py's own "never repeat the same tool with the
    same input" rule is advisory text the model doesn't reliably follow.

    The fix must not be zero-tolerance, though: the original
    app/core/prompts.py design explicitly allowed a tool+input pair to run
    "not more than TWICE" - a model that doubts a result (e.g. a transient
    network blip) needs room for one real retry. Only a THIRD identical
    attempt should be blocked."""
    llm = MockLLM([
        "Thought: Scan first.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Scan again just to be safe.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Scan a third time.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Understood, wrapping up.\nFinal Answer: Security report here.",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Security report here.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    # mock_scan must have been executed exactly twice (the allowed retry),
    # not three times - the third identical call should have been blocked
    # before reaching execute_node.
    tool_messages = [m for m in result["messages"] if "Open ports" in str(m.content)]
    assert len(tool_messages) == 2, f"mock_scan's real result should appear twice, got {len(tool_messages)}"

    # The model must have been told about the block, not left guessing.
    blocked_msgs = [m for m in result["messages"] if "already called" in str(m.content)]
    assert len(blocked_msgs) == 1, "Model should receive exactly one duplicate-call warning"

    assert result["phase"] == "done"
    assert "Final Answer:" in result["messages"][-1].content
    print("  [PASS] test_custom_graph_allows_one_retry_before_blocking_third_identical_call")


def test_custom_graph_duplicate_call_loop_respects_max_iterations():
    """A model that keeps re-proposing the same call forever - even past its
    one allowed retry - must still terminate at max_iterations, same as the
    format_error loop."""
    llm = MockLLM([
        "Thought: Scan.\nAction: mock_scan\nAction Input: https://test.com",
    ])

    state = dict(BASE_STATE)
    state["max_iterations"] = 3

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(state)

    assert result["iteration_count"] <= state["max_iterations"]
    assert result["phase"] != "done"
    print(f"  [PASS] test_custom_graph_duplicate_call_loop_respects_max_iterations (stopped at {result['iteration_count']})")


def test_check_early_termination_detects_flag():
    """Verify Check early termination detects flag."""
    assert _check_early_termination("here is the flag{abc123} you wanted") == "flag{abc123}"
    print("  [PASS] test_check_early_termination_detects_flag")


def test_check_early_termination_no_match_returns_none():
    """Verify Check early termination no match returns none."""
    assert _check_early_termination("no flag here, just a normal result") is None
    print("  [PASS] test_check_early_termination_no_match_returns_none")


def test_build_reflection_note_blocked_response_suggests_bypass():
    """Verify Build reflection note blocked response suggests bypass."""
    note = _build_reflection_note("Advanced_Evasion_Probe::x", "HTTP 403 Forbidden - blocked by WAF")
    assert "bypass" in note.lower() or "encoding" in note.lower()
    print("  [PASS] test_build_reflection_note_blocked_response_suggests_bypass")


def test_build_reflection_note_generic_response_suggests_different_input():
    """Verify Build reflection note generic response suggests different input."""
    note = _build_reflection_note("mock_scan::x", "some ordinary, unremarkable output")
    assert "genuinely different" in note.lower()
    print("  [PASS] test_build_reflection_note_generic_response_suggests_different_input")


def test_inter_reflect_majority_yes():
    """Verify Inter reflect majority yes."""
    llm = ReflectionAwareMockLLM([], vote_responses=["yes", "no", "yes"])
    assert _inter_reflect(llm, "Run_Nikto::x", "some result") is True
    print("  [PASS] test_inter_reflect_majority_yes")


def test_inter_reflect_majority_no():
    """Verify Inter reflect majority no."""
    llm = ReflectionAwareMockLLM([], vote_responses=["no", "no", "yes"])
    assert _inter_reflect(llm, "Run_Nikto::x", "some result") is False
    print("  [PASS] test_inter_reflect_majority_no")


def test_inter_reflect_returns_none_when_all_calls_fail():
    """Verify Inter reflect returns none when all calls fail."""
    class _FailingLLM:
        def invoke(self, messages, **kwargs):
            """Invoke."""
            raise RuntimeError("unreachable")
    assert _inter_reflect(_FailingLLM(), "Run_Nikto::x", "result") is None
    print("  [PASS] test_inter_reflect_returns_none_when_all_calls_fail")


def test_duplicate_call_reflection_note_is_response_aware():
    """specs/019 FR-005: the duplicate-call block's guidance must now carry
    a concrete, response-derived suggestion, not just "try something else"."""
    llm = MockLLM([
        "Thought: probe.\nAction: mock_probe\nAction Input: https://test.com",
        "Thought: probe again.\nAction: mock_probe\nAction Input: https://test.com",
        "Thought: probe third time.\nAction: mock_probe\nAction Input: https://test.com",
        "Thought: done.\nFinal Answer: report",
        "Thought: confirmed, no further scanning applies.\nFinal Answer: report",
    ])
    graph = _build_custom_workflow(llm, [mock_probe], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    # 2 reflection notes now: the duplicate-call Intra-reflection note (FR-005)
    # and the phase5/6 nudge (mock_probe isn't a Phase 5/6 tool either).
    reflection_notes = result.get("reflection_notes", [])
    assert len(reflection_notes) == 2
    assert "blocked" in reflection_notes[0].lower() or "bypass" in reflection_notes[0].lower()

    blocked_msgs = [m for m in result["messages"] if "already called" in str(m.content)]
    assert len(blocked_msgs) == 1
    assert "Reflection:" in blocked_msgs[0].content
    print("  [PASS] test_duplicate_call_reflection_note_is_response_aware")


def test_inter_reflection_majority_success_appends_note():
    """Verify Inter reflection majority success appends note."""
    llm = ReflectionAwareMockLLM(
        react_responses=[
            "Thought: scan.\nAction: Run_Nikto\nAction Input: https://test.com",
            "Thought: done.\nFinal Answer: report",
        ],
        vote_responses=["yes", "yes", "no"],
    )
    graph = _build_custom_workflow(llm, [Run_Nikto], enable_inter_reflection=True)
    result = graph.invoke(dict(BASE_STATE))

    assert llm.vote_call_count == 3
    reflect_msgs = [m for m in result["messages"] if "majority-vote assessment" in str(m.content)]
    assert len(reflect_msgs) == 1
    assert "SUCCESS" in reflect_msgs[0].content
    print("  [PASS] test_inter_reflection_majority_success_appends_note")


def test_inter_reflection_majority_inconclusive_appends_note():
    """Verify Inter reflection majority inconclusive appends note."""
    llm = ReflectionAwareMockLLM(
        react_responses=[
            "Thought: scan.\nAction: Run_Nikto\nAction Input: https://test.com",
            "Thought: done.\nFinal Answer: report",
        ],
        vote_responses=["no", "no", "yes"],
    )
    graph = _build_custom_workflow(llm, [Run_Nikto], enable_inter_reflection=True)
    result = graph.invoke(dict(BASE_STATE))

    reflect_msgs = [m for m in result["messages"] if "majority-vote assessment" in str(m.content)]
    assert len(reflect_msgs) == 1
    assert "INCONCLUSIVE" in reflect_msgs[0].content
    print("  [PASS] test_inter_reflection_majority_inconclusive_appends_note")


def test_inter_reflection_disabled_skips_majority_vote():
    """specs/019 NFR-002 escape hatch: enable_inter_reflection=False must
    restore the exact pre-specs/019 single-pass behavior for EXPLOITATION_TOOLS."""
    llm = ReflectionAwareMockLLM(
        react_responses=[
            "Thought: scan.\nAction: Run_Nikto\nAction Input: https://test.com",
            "Thought: done.\nFinal Answer: report",
        ],
        vote_responses=["yes", "yes", "yes"],
    )
    graph = _build_custom_workflow(llm, [Run_Nikto], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    assert llm.vote_call_count == 0, "no votes should be cast when disabled"
    reflect_msgs = [m for m in result["messages"] if "majority-vote assessment" in str(m.content)]
    assert len(reflect_msgs) == 0
    print("  [PASS] test_inter_reflection_disabled_skips_majority_vote")


def test_early_termination_flag_detection_adds_nudge():
    """Verify Early termination flag detection adds nudge."""
    llm = MockLLM([
        "Thought: read file.\nAction: mock_flag_tool\nAction Input: https://test.com",
        "Thought: done.\nFinal Answer: flag{argus_test_flag_123}",
        "Thought: confirmed, no further scanning applies.\nFinal Answer: flag{argus_test_flag_123}",
    ])
    graph = _build_custom_workflow(llm, [mock_flag_tool], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    nudge_msgs = [m for m in result["messages"] if "flag-shaped string" in str(m.content)]
    assert len(nudge_msgs) == 1
    assert "flag{argus_test_flag_123}" in nudge_msgs[0].content
    print("  [PASS] test_early_termination_flag_detection_adds_nudge")


def test_final_answer_without_phase56_tool_gets_nudged_once_then_accepted():
    """Rule 5 ("attempt Phase 5/6 before a Final Answer") was advisory text
    only - a live run against scanme.nmap.org concluded after just
    Check_Reachability/Subdomain_Enumeration/Recon_Suite, never touching
    Run_Nikto/Run_FFUF/Exploit_Suggester/Advanced_Evasion_Probe, because
    nothing enforced it. This is a one-time nudge, not a hard block: the
    model gets one chance to reconsider, then its second Final Answer is
    accepted even without a Phase 5/6 tool call."""
    llm = MockLLM([
        "Thought: scan.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: done already.\nFinal Answer: first attempt",
        "Thought: ok, taking that into account.\nFinal Answer: second attempt",
    ])
    graph = _build_custom_workflow(llm, [mock_scan], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    nudge_msgs = [m for m in result["messages"] if "vulnerability scanning or exploitation" in str(m.content)]
    assert len(nudge_msgs) == 1, "should nudge exactly once, not repeatedly"
    assert result["phase"] == "done"
    assert "second attempt" in result["messages"][-1].content
    print("  [PASS] test_final_answer_without_phase56_tool_gets_nudged_once_then_accepted")


def test_final_answer_with_phase56_tool_is_not_nudged():
    """Verify Final answer with phase56 tool is not nudged."""
    llm = MockLLM([
        "Thought: scan.\nAction: Run_Nikto\nAction Input: https://test.com",
        "Thought: done.\nFinal Answer: report after nikto",
    ])
    graph = _build_custom_workflow(llm, [Run_Nikto], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    nudge_msgs = [m for m in result["messages"] if "vulnerability scanning or exploitation" in str(m.content)]
    assert len(nudge_msgs) == 0
    assert result["phase"] == "done"
    assert "report after nikto" in result["messages"][-1].content
    print("  [PASS] test_final_answer_with_phase56_tool_is_not_nudged")


def test_final_answer_with_zero_tool_calls_is_not_nudged():
    """A Final Answer with no tool calls at all is a different, broader
    problem (skipping every phase) - out of scope for this specific check,
    so it must not be nudged by this mechanism."""
    llm = MockLLM([
        "Thought: I already know enough.\nFinal Answer: immediate answer",
    ])
    graph = _build_custom_workflow(llm, [mock_scan], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    nudge_msgs = [m for m in result["messages"] if "vulnerability scanning or exploitation" in str(m.content)]
    assert len(nudge_msgs) == 0
    assert result["phase"] == "done"
    print("  [PASS] test_final_answer_with_zero_tool_calls_is_not_nudged")


def test_custom_graph_handles_unknown_tool():
    """Verify custom graph handles unknown tool names gracefully."""
    llm = MockLLM([
        "Thought: Try unknown.\nAction: UnknownTool\nAction Input: test",
        "Thought: Switch to scan.\nAction: mock_scan\nAction Input: test",
        "Thought: Done.\nFinal Answer: Done.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    # Should have an error message in the messages
    error_msgs = [m for m in result["messages"] if "Unknown tool" in str(m.content)]
    assert len(error_msgs) > 0, "Should have error message for unknown tool"
    print("  [PASS] test_custom_graph_handles_unknown_tool")


def test_custom_graph_immediate_final_answer():
    """Verify graph ends immediately if LLM outputs Final Answer first."""
    llm = MockLLM([
        "Final Answer: Target is clean. No issues found.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 1, f"Expected 1, got {result['iteration_count']}"
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_immediate_final_answer")


def test_custom_graph_no_output_fallback():
    """Verify graph handles empty LLM response.

    mock_scan isn't a Phase 5/6 tool, so the first Final Answer absorbs one
    specs/019 phase5/6 nudge before the second is accepted."""
    llm = MockLLM([
        "",
        "Thought: Try again.\nAction: mock_scan\nAction Input: test",
        "Final Answer: Done.",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))
    assert result["iteration_count"] <= 4, f"Should stop, got {result['iteration_count']}"
    print("  [PASS] test_custom_graph_no_output_fallback")


# -- JSON Action format tests --------------------------

def test_custom_graph_json_action_format():
    """Verify parser handles JSON Action format.

    Neither mock_scan nor mock_search is a Phase 5/6 tool, so the first
    Final Answer absorbs one specs/019 phase5/6 nudge."""
    llm = MockLLM([
        'Thought: Scanning.\nAction: {"name": "mock_scan", "input": "https://test.com"}\n',
        'Thought: Searching.\nAction: {"name": "mock_search", "input": "nginx 1.24"}\n',
        "Final Answer: Report done.",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Report done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan, mock_search])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 4
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_json_action_format")


def test_custom_graph_json_action_variants():
    """Verify parser accepts alternative JSON key names (action, tool, arguments).

    mock_scan isn't a Phase 5/6 tool, so the first Final Answer absorbs one
    specs/019 phase5/6 nudge."""
    llm = MockLLM([
        'Thought: Scan.\nAction: {"action": "mock_scan", "arguments": "https://test.com"}\n',
        "Final Answer: Done.",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 3
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_json_action_variants")


def test_custom_graph_malformed_json_fallback_to_text():
    """Verify parser falls back to text format when JSON is malformed.

    mock_scan isn't a Phase 5/6 tool, so the first Final Answer absorbs one
    specs/019 phase5/6 nudge."""
    llm = MockLLM([
        'Thought: Scan.\nAction: {"name": "mock_scan" "input": "missing comma"}\n',  # malformed JSON
        'Thought: Fixed.\nAction: mock_scan\nAction Input: https://test.com',
        "Final Answer: Done.",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] <= 4
    # Should have executed mock_scan successfully via text fallback
    assert "Open ports" in str(result["tool_result"])
    print("  [PASS] test_custom_graph_malformed_json_fallback_to_text")


def test_structured_action_produces_tool_call():
    """format=json path (012 FR-C9): structured Action maps to an Action: line
    that parse_node's regex parser can consume unchanged."""
    llm = StructuredMockLLM(_ArgusAction(thought="Scan first.", tool="mock_scan", input="https://test.com"))
    content = _try_structured_action(llm, "system prompt", [HumanMessage(content="go")])
    assert content is not None
    assert 'Action: {"name": "mock_scan", "input": "https://test.com"}' in content


def test_structured_action_produces_final_answer():
    """Verify Structured action produces final answer."""
    llm = StructuredMockLLM(_ArgusAction(thought="Done.", final_answer="Security report here."))
    content = _try_structured_action(llm, "system prompt", [HumanMessage(content="go")])
    assert content == "Thought: Done.\nFinal Answer: Security report here."


def test_structured_action_falls_back_when_unsupported():
    """012 FR-C10: models without with_structured_output fall back silently."""
    llm = MockLLM(["Thought: x\nFinal Answer: y"])
    assert _try_structured_action(llm, "system prompt", [HumanMessage(content="go")]) is None


def test_structured_action_falls_back_on_exception():
    """012 FR-C10: a model that claims to support format=json but errors falls back."""
    llm = StructuredMockLLM(raise_on_structured=True)
    assert _try_structured_action(llm, "system prompt", [HumanMessage(content="go")]) is None


def test_custom_graph_uses_structured_action_end_to_end():
    """Full graph cycle driven by structured decoding instead of free-text output."""
    llm = StructuredMockLLM(_ArgusAction(thought="Done.", final_answer="Security report here."))
    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 1
    assert "Security report here." in result["messages"][-1].content
    print("  [PASS] test_custom_graph_uses_structured_action_end_to_end")


def test_custom_graph_format_error_loop_respects_max_iterations():
    """specs/018 regression test - bug fix in route_after_parse.

    Previously the format_error branch routed straight back to "agent" with
    NO max_iterations check at all (unlike the tool-execute path), unbounded
    except by LangGraph's default recursion_limit (25), via an ungraceful
    GraphRecursionError rather than a clean stop. This is exactly the failure
    mode from the live incident: a model that never once produces a valid
    Thought/Action/Final Answer line.
    """
    llm = MockLLM(["this is not ReAct-formatted output at all, just prose"])
    state = dict(BASE_STATE)
    state["max_iterations"] = 3

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(state)

    assert result["iteration_count"] <= state["max_iterations"], \
        f"iteration_count {result['iteration_count']} exceeded max {state['max_iterations']}"
    assert result.get("phase") != "done"
    print(f"  [PASS] test_custom_graph_format_error_loop_respects_max_iterations (stopped at {result['iteration_count']})")


def test_structured_final_answer_extracts_security_report():
    """Verify Structured final answer extracts security report."""
    from app.core.schemas import SecurityReport
    report = SecurityReport(
        summary="ok", attack_surface_stats="1 host", findings=[],
        overall_risk_score=4, next_steps=["step1"], output="full text",
    )
    llm = StructuredMockLLM(report)

    result = _try_structured_final_answer(llm, "some raw final answer text")

    assert result is not None
    assert result["overall_risk_score"] == 4
    print("  [PASS] test_structured_final_answer_extracts_security_report")


def test_structured_final_answer_falls_back_when_unsupported():
    """Verify Structured final answer falls back when unsupported."""
    llm = MockLLM(["plain text"])
    assert _try_structured_final_answer(llm, "raw text") is None
    print("  [PASS] test_structured_final_answer_falls_back_when_unsupported")


def test_structured_final_answer_falls_back_on_exception():
    """Verify Structured final answer falls back on exception."""
    llm = StructuredMockLLM(raise_on_structured=True)
    assert _try_structured_final_answer(llm, "raw text") is None
    print("  [PASS] test_structured_final_answer_falls_back_on_exception")


# =======================================================

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print("Argus LangGraph Workflow Tests")
    print(f"{'='*50}\n")

    test_tool_map_building()
    test_target_extraction()
    test_custom_graph_full_cycle()
    test_custom_graph_stops_at_max_iterations()
    test_check_early_termination_detects_flag()
    test_check_early_termination_no_match_returns_none()
    test_build_reflection_note_blocked_response_suggests_bypass()
    test_build_reflection_note_generic_response_suggests_different_input()
    test_inter_reflect_majority_yes()
    test_inter_reflect_majority_no()
    test_inter_reflect_returns_none_when_all_calls_fail()
    test_duplicate_call_reflection_note_is_response_aware()
    test_inter_reflection_majority_success_appends_note()
    test_inter_reflection_majority_inconclusive_appends_note()
    test_inter_reflection_disabled_skips_majority_vote()
    test_early_termination_flag_detection_adds_nudge()
    test_final_answer_without_phase56_tool_gets_nudged_once_then_accepted()
    test_final_answer_with_phase56_tool_is_not_nudged()
    test_final_answer_with_zero_tool_calls_is_not_nudged()
    test_custom_graph_handles_unknown_tool()
    test_custom_graph_immediate_final_answer()
    test_custom_graph_no_output_fallback()
    test_custom_graph_json_action_format()
    test_custom_graph_json_action_variants()
    test_custom_graph_malformed_json_fallback_to_text()
    test_structured_action_produces_tool_call()
    test_structured_action_produces_final_answer()
    test_structured_action_falls_back_when_unsupported()
    test_structured_action_falls_back_on_exception()
    test_custom_graph_uses_structured_action_end_to_end()
    test_custom_graph_format_error_loop_respects_max_iterations()
    test_structured_final_answer_extracts_security_report()
    test_structured_final_answer_falls_back_when_unsupported()
    test_structured_final_answer_falls_back_on_exception()

    print(f"\n{'='*50}")
    print("ALL TESTS PASSED")
    print(f"{'='*50}")
