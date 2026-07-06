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
    _build_tool_map,
    _supports_tool_calls,
    _try_structured_action,
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
                return response

        return _Bound()

    def invoke(self, messages, **kwargs):
        return AIMessage(content="Thought: fallback path used.\nFinal Answer: fallback report")


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
    """Verify custom ReAct graph runs a complete scan->search->report cycle."""
    llm = MockLLM([
        "Thought: Scan first.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Now search CVEs.\nAction: mock_search\nAction Input: nginx",
        "Thought: Done.\nFinal Answer: Security report here.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan, mock_search])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 3, f"Expected 3, got {result['iteration_count']}"
    assert len(result["messages"]) == 6, f"Expected 6 messages, got {len(result['messages'])}"

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
    """Verify graph handles empty LLM response."""
    llm = MockLLM([
        "",
        "Thought: Try again.\nAction: mock_scan\nAction Input: test",
        "Final Answer: Done.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))
    assert result["iteration_count"] <= 3, f"Should stop, got {result['iteration_count']}"
    print("  [PASS] test_custom_graph_no_output_fallback")


# -- JSON Action format tests --------------------------

def test_custom_graph_json_action_format():
    """Verify parser handles JSON Action format."""
    llm = MockLLM([
        'Thought: Scanning.\nAction: {"name": "mock_scan", "input": "https://test.com"}\n',
        'Thought: Searching.\nAction: {"name": "mock_search", "input": "nginx 1.24"}\n',
        "Final Answer: Report done.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan, mock_search])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 3
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_json_action_format")


def test_custom_graph_json_action_variants():
    """Verify parser accepts alternative JSON key names (action, tool, arguments)."""
    llm = MockLLM([
        'Thought: Scan.\nAction: {"action": "mock_scan", "arguments": "https://test.com"}\n',
        "Final Answer: Done.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 2
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_json_action_variants")


def test_custom_graph_malformed_json_fallback_to_text():
    """Verify parser falls back to text format when JSON is malformed."""
    llm = MockLLM([
        'Thought: Scan.\nAction: {"name": "mock_scan" "input": "missing comma"}\n',  # malformed JSON
        'Thought: Fixed.\nAction: mock_scan\nAction Input: https://test.com',
        "Final Answer: Done.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] <= 3
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


# =======================================================

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print("Argus LangGraph Workflow Tests")
    print(f"{'='*50}\n")

    test_tool_map_building()
    test_target_extraction()
    test_custom_graph_full_cycle()
    test_custom_graph_stops_at_max_iterations()
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

    print(f"\n{'='*50}")
    print("ALL TESTS PASSED")
    print(f"{'='*50}")
