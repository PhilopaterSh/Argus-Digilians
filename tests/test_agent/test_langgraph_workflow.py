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

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from app.core.agent.react_workflow import (
    _already_confirmed_exploitation,
    _ArgusAction,
    _bounded_observation,
    _build_custom_workflow,
    _build_multi_role_workflow,
    _build_prebuilt_workflow,
    _build_reflection_note,
    _build_tool_map,
    _check_early_termination,
    _extract_vulnerability_hints,
    _hostname,
    _inter_reflect,
    _is_out_of_scope,
    _live_test_directive,
    _matched_vuln_keywords,
    _PlannerDecision,
    _supports_tool_calls,
    _try_planner_decision,
    _try_structured_action,
    _try_structured_final_answer,
    extract_target,
    OBSERVATION_MAX_CHARS,
)
from app.core.agent.react_state import ArgusAgentState

pytestmark = pytest.mark.unit


# -- Mock helpers -------------------------------------
class MockLLM:
    """A mock LLM that returns predetermined ReAct-format responses."""
    def __init__(self, responses: list[str]):
        """Store the scripted responses to cycle through.

        Args:
            responses (list[str]): ReAct-format response texts, cycled
                in order (wrapping around) on each `invoke()` call.
        """
        self.responses = responses
        self.call_count = 0

    def invoke(self, messages, **kwargs):
        """Return the next scripted response, cycling back to the start when exhausted.

        Args:
            messages: Unused - accepted for LLM-interface compatibility.
            **kwargs: Unused - accepted for LLM-interface compatibility.

        Returns:
            AIMessage: The next entry in `self.responses`.
        """
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
        """Store the canned structured response (or a raise-on-bind flag).

        Args:
            structured_response: The object `with_structured_output(...)
                .invoke()` will return.
            raise_on_structured (bool): If True, `with_structured_output`
                raises instead, simulating a model without format=json support.
        """
        self._structured_response = structured_response
        self._raise = raise_on_structured

    def with_structured_output(self, schema):
        """Bind a schema, returning an object whose invoke() yields the canned response.

        Args:
            schema: Unused - accepted for LLM-interface compatibility.

        Returns:
            An object with an `invoke(messages)` method returning
            `self._structured_response`.

        Raises:
            RuntimeError: If constructed with `raise_on_structured=True`.
        """
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
        """Store the two independent response scripts.

        Args:
            react_responses (list[str]): Cycled responses for ordinary
                ReAct action-generation calls.
            vote_responses (list[str] | None): Cycled responses for
                `_inter_reflect`'s yes/no majority-vote prompt; defaults
                to an empty list.
        """
        self.react_responses = react_responses
        self.vote_responses = vote_responses or []
        self.react_call_count = 0
        self.vote_call_count = 0

    def invoke(self, messages, **kwargs):
        """Answer from vote_responses if this looks like a reflection
        vote prompt, else cycle through react_responses.

        Args:
            messages: Message list; the last message's content is
                checked for the reflection-vote marker text.
            **kwargs: Unused - accepted for LLM-interface compatibility.

        Returns:
            AIMessage: The next scripted response from whichever script matched.
        """
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


def Advanced_Evasion_Probe(target: str) -> str:
    """Stands in for the real Advanced_Evasion_Probe tool - same name, so
    it's recognised by react_workflow.py's `_LIVE_TEST_TOOLS`/
    `EXPLOITATION_TOOLS` allowlists. Returns the exact success shape
    app/tools/evasion.py's advanced_vuln_probe() produces on a confirmed
    hit (the "ADVANCED EVASION PROBE REPORT" header only appears when a
    payload actually succeeded), so tests can exercise
    `_already_confirmed_exploitation()` against realistic text instead of
    a synthetic marker."""
    return (
        "--- [SHIELD] ADVANCED EVASION PROBE REPORT ---\n"
        "[!] Path Traversal Success (../../../../etc/passwd): "
        "LFI/Path Traversal Confirmed (/etc/passwd read success)\n"
        "    [camera] Screenshot saved: artifacts/screenshots/"
        "path_traversal_test.com_20260823_000000_000000_response.png"
    )


def mock_flag_tool(target: str) -> str:
    """Returns a flag-shaped string - used to test early-termination detection."""
    return "Retrieved file contents: flag{argus_test_flag_123}"


def mock_title_tool(target: str) -> str:
    """Returns a whatweb-style tech fingerprint with a Title[...] match -
    used to test the deterministic vulnerability-hint evidence scan (see
    _extract_vulnerability_hints), reproducing the real live-run signal a
    PortSwigger lab's Recon_Suite output contained."""
    return "Tech: https://test.com [200 OK] Title[File path traversal, simple case]"


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

# specs/020 (multi-agent role separation, feature-flagged off by default)
MULTI_ROLE_BASE_STATE = {
    **BASE_STATE,
    "reflection_notes": [],
    "current_role": "",
    "role_history": [],
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

    Neither mock_scan nor mock_search is a Phase 1-2 or Phase 5/6 tool, so
    the first "Final Answer" absorbs the 2026-07-26 phase12 nudge, the
    second absorbs the specs/019 phase5/6 nudge, before the third Final
    Answer is finally accepted."""
    llm = MockLLM([
        "Thought: Scan first.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Now search CVEs.\nAction: mock_search\nAction Input: nginx",
        "Thought: Done.\nFinal Answer: Security report here.",
        "Thought: Still nothing else to add.\nFinal Answer: Security report here (again).",
        "Thought: Understood, no further scanning applies.\nFinal Answer: Security report here (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan, mock_search])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 5, f"Expected 5, got {result['iteration_count']}"

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
    attempt should be blocked.

    mock_scan isn't a Phase 1-2 or Phase 5/6 tool, so the first Final
    Answer absorbs the 2026-07-26 phase12 nudge, the second absorbs the
    specs/019 phase5/6 nudge, before the third is finally accepted."""
    llm = MockLLM([
        "Thought: Scan first.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Scan again just to be safe.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Scan a third time.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Understood, wrapping up.\nFinal Answer: Security report here.",
        "Thought: Still nothing else to add.\nFinal Answer: Security report here (again).",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Security report here (confirmed).",
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


def test_custom_graph_blocks_near_duplicate_call_differing_only_by_trailing_slash():
    """2026-07-25 regression (web-research-backed follow-up to
    MAX_CONSECUTIVE_DUPLICATE_BLOCKS, see _normalize_call_input()'s own
    comment): the duplicate-call guard used to compare tool_input via exact
    string equality only, so "https://test.com" and "https://test.com/" (a
    trailing slash - a real, common way an LLM restates the same target)
    never registered as the same call at all, silently bypassing the guard
    rather than tripping it - one credible way a real run could reach 18
    Recon_Suite calls despite the guard's own "block the 3rd identical
    attempt" design. _normalize_call_input() now strips a single trailing
    slash before comparison, so this must be caught exactly like an exact
    repeat."""
    # Three trailing "Final Answer" entries (mirroring
    # test_custom_graph_allows_one_retry_before_blocking_third_identical_call's
    # own pattern): mock_scan is neither a Phase 1-2 nor a Phase 5/6 tool, so
    # the first Final Answer absorbs the 2026-07-26 phase12 nudge, the
    # second absorbs the specs/019 phase5/6 nudge, before the third can
    # truly end the run - without enough queued up, MockLLM's cycling would
    # replay the scan actions again and confound this test with an unrelated
    # 3rd-consecutive-block scenario.
    llm = MockLLM([
        "Thought: Scan first.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: Scan again, just with a trailing slash.\nAction: mock_scan\nAction Input: https://test.com/",
        "Thought: One more identical attempt.\nAction: mock_scan\nAction Input: https://test.com/",
        "Thought: Understood, wrapping up.\nFinal Answer: Security report here.",
        "Thought: Still nothing else to add.\nFinal Answer: Security report here (again).",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Security report here (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    # mock_scan's real result should appear exactly twice (the allowed
    # retry) even though the 2nd call's raw tool_input string differs from
    # the 1st by a trailing slash - normalization must recognise them as
    # the same call, so the 3rd (identical to the 2nd) gets blocked.
    tool_messages = [m for m in result["messages"] if "Open ports" in str(m.content)]
    assert len(tool_messages) == 2, f"trailing-slash near-duplicate should still count as the same call, got {len(tool_messages)}"

    blocked_msgs = [m for m in result["messages"] if "already called" in str(m.content)]
    assert len(blocked_msgs) == 1, "the near-duplicate (trailing slash) call should have been blocked"

    print("  [PASS] test_custom_graph_blocks_near_duplicate_call_differing_only_by_trailing_slash")


def test_hostname_extracts_from_full_url_and_bare_domain():
    """_hostname must handle both a full http(s):// URL and a bare domain
    (Recon_Suite/Check_Reachability are sometimes called with just the
    domain, no scheme)."""
    assert _hostname("https://0a0600b3031358e982cd9c740003002e.web-security-academy.net/") == \
        "0a0600b3031358e982cd9c740003002e.web-security-academy.net"
    assert _hostname("0a0600b3031358e982cd9c740003002e.web-security-academy.net") == \
        "0a0600b3031358e982cd9c740003002e.web-security-academy.net"
    assert _hostname("https://test.com:8080/path?x=1") == "test.com"
    assert _hostname("SQL injection findings for this target") is None
    assert _hostname("") is None
    assert _hostname(None) is None
    print("  [PASS] test_hostname_extracts_from_full_url_and_bare_domain")


def test_is_out_of_scope_catches_hallucinated_target_swap():
    """2026-08-01: locks in the fix for the b84499b0 live-run failure -
    when the duplicate-call guard told the model to "try a genuinely
    different input", it invented an entirely different, unauthorized
    web-security-academy.net hostname instead of varying the technique
    against the real target. _is_out_of_scope must catch this exact case,
    while never flagging a same-host variation (different path/param) or a
    non-URL input (e.g. a Query_Memory search term) as out of scope."""
    target = "https://0a0600b3031358e982cd9c740003002e.web-security-academy.net/"

    hallucinated = "https://0a1300960402886e823a83f000260093.web-security-academy.net"
    assert _is_out_of_scope(hallucinated, target) is True

    same_host_diff_path = (
        "https://0a0600b3031358e982cd9c740003002e.web-security-academy.net"
        "/image?filename=../../etc/passwd"
    )
    assert _is_out_of_scope(same_host_diff_path, target) is False

    assert _is_out_of_scope("evil-unrelated-domain.com", target) is True
    assert _is_out_of_scope("SQL injection findings for this target", target) is False
    print("  [PASS] test_is_out_of_scope_catches_hallucinated_target_swap")


_recon_call_log = []


def mock_recon_returns_hallucinated_target_on_retry(target: str) -> str:
    """Records every input it's actually invoked with (module-level
    `_recon_call_log`) so the test below can assert the fabricated,
    unauthorized hostname never reached the tool itself - not just that
    execute_node emitted a rejection message. Mirrors the scenario observed
    live in run b84499b0: the model swapped in a fabricated hostname
    instead of varying its technique on the real target."""
    _recon_call_log.append(target)
    return "Tech fingerprint: some real recon output for the authorized target."


def test_custom_graph_rejects_hallucinated_target_swap_without_executing_tool():
    """Graph-level regression for the b84499b0 failure: once the duplicate
    guard blocks a repeat, a swapped-in unauthorized hostname must be
    rejected by execute_node BEFORE the tool runs (no network cost, no
    fabricated-target Recon_Suite call), not merely flagged after the
    fact."""
    _recon_call_log.clear()
    llm = MockLLM([
        "Thought: Recon first.\nAction: mock_recon_returns_hallucinated_target_on_retry\nAction Input: https://test.com",
        "Thought: Recon again, same input.\nAction: mock_recon_returns_hallucinated_target_on_retry\nAction Input: https://test.com",
        "Thought: Try a different target entirely.\nAction: mock_recon_returns_hallucinated_target_on_retry\nAction Input: https://evil-unrelated-domain.com",
        "Thought: Understood, wrapping up.\nFinal Answer: Security report here.",
        "Thought: Still nothing else to add.\nFinal Answer: Security report here (again).",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Security report here (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_recon_returns_hallucinated_target_on_retry])
    result = graph.invoke(dict(BASE_STATE))

    rejected_msgs = [m for m in result["messages"] if "REJECTED" in str(m.content)]
    assert len(rejected_msgs) == 1, "the hallucinated-hostname call should have been rejected exactly once"
    # The 2nd (identical) call is allowed as the one free retry before the
    # duplicate guard would block a 3rd identical repeat - so the real tool
    # legitimately runs twice with the authorized host. What matters here:
    # the fabricated hostname never appears in that call log at all.
    assert _recon_call_log == ["https://test.com", "https://test.com"], (
        f"the out-of-scope call must never actually reach the tool - got calls: {_recon_call_log}"
    )
    assert "evil-unrelated-domain.com" not in _recon_call_log
    print("  [PASS] test_custom_graph_rejects_hallucinated_target_swap_without_executing_tool")


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


def test_custom_graph_gives_up_early_after_consecutive_duplicate_blocks():
    """2026-07-25 regression: a live run against a real PortSwigger lab
    called Recon_Suite twice (the guard's own allowed retry), got blocked
    on the third identical attempt as designed, then kept re-proposing the
    same blocked call ~15 times in a row - each block producing the exact
    same guidance message, since the guard's own hard block guarantees an
    identical outcome every time - burning the entire max_iterations=25
    budget before finally reporting a bare "no_final_answer" error with no
    indication of what was actually tried.

    With a generous max_iterations budget (25, matching the live incident),
    the graph must now conclude early - once
    MAX_CONSECUTIVE_DUPLICATE_BLOCKS consecutive blocks occur - with an
    honest, partial Final Answer describing what was tried, rather than
    exhausting the full budget on a conversation that provably cannot
    change outcome."""
    llm = MockLLM([
        "Thought: Scan.\nAction: mock_scan\nAction Input: https://test.com",
    ])
    state = dict(BASE_STATE)
    state["max_iterations"] = 25

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(state)

    assert result["phase"] == "done", "Should conclude early with an honest partial answer, not spin to max_iterations"
    last_content = result["messages"][-1].content
    assert "Final Answer:" in last_content
    assert "stopped early" in last_content
    assert "mock_scan" in last_content
    # 2 allowed real executions + a small, bounded number of blocked turns
    # before giving up - well under the 25-iteration budget this regression
    # previously exhausted completely.
    assert result["iteration_count"] < 10, (
        f"Expected to give up well before max_iterations=25, got {result['iteration_count']}"
    )
    print(f"  [PASS] test_custom_graph_gives_up_early_after_consecutive_duplicate_blocks (stopped at {result['iteration_count']})")


def test_custom_graph_recovering_between_blocks_resets_consecutive_counter():
    """A model that gets blocked once, then genuinely recovers with a
    different real action, then later gets blocked again on a (possibly
    different) repeat must NOT have its consecutive-block count carried
    over from the earlier, already-resolved block - only a truly
    uninterrupted streak of blocks should trigger the early give-up."""
    # mock_scan/mock_search are neither Phase 1-2 nor Phase 5/6 tools, so the
    # first Final Answer absorbs the 2026-07-26 phase12 nudge and the second
    # absorbs the specs/019 phase5/6 nudge before the third is accepted.
    llm = MockLLM([
        "Thought: Scan.\nAction: mock_scan\nAction Input: https://test.com",       # 1: real exec #1
        "Thought: Scan again.\nAction: mock_scan\nAction Input: https://test.com",  # 2: real exec #2 (allowed retry)
        "Thought: Scan once more.\nAction: mock_scan\nAction Input: https://test.com",  # 3: BLOCKED (consecutive=1)
        "Thought: Search instead.\nAction: mock_search\nAction Input: nginx",       # 4: real, different action - resets counter
        "Thought: Done.\nFinal Answer: Security report here.",
        "Thought: Still nothing else to add.\nFinal Answer: Security report here (still).",
        "Thought: Confirmed.\nFinal Answer: Security report here (confirmed).",
    ])
    state = dict(BASE_STATE)
    state["max_iterations"] = 15

    graph = _build_custom_workflow(llm, [mock_scan, mock_search])
    result = graph.invoke(state)

    assert result["phase"] == "done"
    last_content = result["messages"][-1].content
    assert "Final Answer:" in last_content
    # The real Final Answer text must be present - NOT the early-give-up
    # synthesized note, proving the single intervening block didn't
    # accumulate toward MAX_CONSECUTIVE_DUPLICATE_BLOCKS once real progress
    # (mock_search) happened in between.
    assert "stopped early" not in last_content
    assert "Security report here" in last_content
    print("  [PASS] test_custom_graph_recovering_between_blocks_resets_consecutive_counter")


def test_check_early_termination_detects_flag():
    """Verify Check early termination detects flag."""
    assert _check_early_termination("here is the flag{abc123} you wanted") == "flag{abc123}"
    print("  [PASS] test_check_early_termination_detects_flag")


def test_extract_vulnerability_hints_detects_title_pattern():
    """Verify Extract vulnerability hints detects title pattern."""
    hints = _extract_vulnerability_hints("Tech: [200 OK] Title[File path traversal, simple case]")
    assert any("File path traversal, simple case" in h for h in hints)
    print("  [PASS] test_extract_vulnerability_hints_detects_title_pattern")


def test_extract_vulnerability_hints_detects_keyword():
    """Verify Extract vulnerability hints detects keyword."""
    hints = _extract_vulnerability_hints("The response body reflects a classic SQL Injection error.")
    assert any("sql injection" in h for h in hints)
    print("  [PASS] test_extract_vulnerability_hints_detects_keyword")


def test_extract_vulnerability_hints_no_match_returns_empty():
    """Verify Extract vulnerability hints no match returns empty."""
    assert _extract_vulnerability_hints("Host is up. Port 80 open, Apache 2.4.") == []
    print("  [PASS] test_extract_vulnerability_hints_no_match_returns_empty")


def test_extract_vulnerability_hints_handles_empty_input():
    """Verify Extract vulnerability hints handles empty input."""
    assert _extract_vulnerability_hints("") == []
    assert _extract_vulnerability_hints(None) == []
    print("  [PASS] test_extract_vulnerability_hints_handles_empty_input")


def test_check_early_termination_no_match_returns_none():
    """Verify Check early termination no match returns none."""
    assert _check_early_termination("no flag here, just a normal result") is None
    print("  [PASS] test_check_early_termination_no_match_returns_none")


def test_bounded_observation_short_result_passes_through_unchanged():
    """Verify Bounded observation short result passes through unchanged."""
    assert _bounded_observation("a short tool result") == "a short tool result"
    print("  [PASS] test_bounded_observation_short_result_passes_through_unchanged")


def test_bounded_observation_oversized_result_is_truncated_with_notice():
    """Live-discovered 2026-07-19: Subdomain_Enumeration against example.com
    returned ~3000 lines, which - before this fix - was passed to the LLM
    unbounded (unlike the parallel tool_result state field, which was
    already truncated) and demonstrably caused the model to hallucinate an
    unrelated vulnerability instead of reasoning about the real recon data."""
    huge_result = "x" * (OBSERVATION_MAX_CHARS + 500)
    bounded = _bounded_observation(huge_result)
    assert len(bounded) < len(huge_result)
    assert bounded.startswith("x" * OBSERVATION_MAX_CHARS)
    assert "truncated" in bounded
    assert "500" in bounded
    print("  [PASS] test_bounded_observation_oversized_result_is_truncated_with_notice")


def test_bounded_observation_coerces_non_string_input():
    """Verify Bounded observation coerces non string input."""
    assert _bounded_observation(12345) == "12345"
    print("  [PASS] test_bounded_observation_coerces_non_string_input")


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
        "Thought: still nothing else.\nFinal Answer: report (again)",
        "Thought: confirmed, no further scanning applies.\nFinal Answer: report (confirmed)",
    ])
    graph = _build_custom_workflow(llm, [mock_probe], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    # 3 reflection notes now: the duplicate-call Intra-reflection note
    # (FR-005), the 2026-07-26 phase12 nudge, and the phase5/6 nudge
    # (mock_probe is neither a Phase 1-2 nor a Phase 5/6 tool).
    reflection_notes = result.get("reflection_notes", [])
    assert len(reflection_notes) == 3
    assert "blocked" in reflection_notes[0].lower() or "bypass" in reflection_notes[0].lower()

    blocked_msgs = [m for m in result["messages"] if "already called" in str(m.content)]
    assert len(blocked_msgs) == 1
    assert "Reflection:" in blocked_msgs[0].content
    print("  [PASS] test_duplicate_call_reflection_note_is_response_aware")


def test_inter_reflection_majority_success_appends_note():
    """Verify Inter reflection majority success appends note.

    Run_Nikto is a Phase 5/6 tool but not a Phase 1-2 tool, so the first
    Final Answer now absorbs the 2026-07-26 phase12 nudge before the
    second is accepted."""
    llm = ReflectionAwareMockLLM(
        react_responses=[
            "Thought: scan.\nAction: Run_Nikto\nAction Input: https://test.com",
            "Thought: done.\nFinal Answer: report",
            "Thought: confirmed.\nFinal Answer: report (confirmed)",
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
    """Verify Inter reflection majority inconclusive appends note.

    Run_Nikto is a Phase 5/6 tool but not a Phase 1-2 tool, so the first
    Final Answer now absorbs the 2026-07-26 phase12 nudge before the
    second is accepted."""
    llm = ReflectionAwareMockLLM(
        react_responses=[
            "Thought: scan.\nAction: Run_Nikto\nAction Input: https://test.com",
            "Thought: done.\nFinal Answer: report",
            "Thought: confirmed.\nFinal Answer: report (confirmed)",
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
    """Verify Early termination flag detection adds nudge.

    mock_flag_tool isn't a Phase 1-2 or Phase 5/6 tool, so the first Final
    Answer absorbs the 2026-07-26 phase12 nudge, the second absorbs the
    specs/019 phase5/6 nudge, before the third is accepted."""
    llm = MockLLM([
        "Thought: read file.\nAction: mock_flag_tool\nAction Input: https://test.com",
        "Thought: done.\nFinal Answer: flag{argus_test_flag_123}",
        "Thought: still nothing else.\nFinal Answer: flag{argus_test_flag_123}",
        "Thought: confirmed, no further scanning applies.\nFinal Answer: flag{argus_test_flag_123}",
    ])
    graph = _build_custom_workflow(llm, [mock_flag_tool], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    nudge_msgs = [m for m in result["messages"] if "flag-shaped string" in str(m.content)]
    assert len(nudge_msgs) == 1
    assert "flag{argus_test_flag_123}" in nudge_msgs[0].content
    print("  [PASS] test_early_termination_flag_detection_adds_nudge")


def test_vulnerability_hint_in_tool_result_adds_directive_nudge():
    """2026-07-11: a live run against a real PortSwigger lab found
    Recon_Suite's own output naming the vulnerability class in a page
    title, and the model never acted on it. This locks in the fix:
    execute_node now surfaces that signal as an explicit reflection note
    instead of relying on the model to notice it unprompted."""
    # mock_title_tool/Run_Nikto together aren't Phase 1-2 tools, so the
    # first Final Answer now absorbs the 2026-07-26 phase12 nudge before
    # the second is accepted.
    llm = MockLLM([
        "Thought: fingerprint the target.\nAction: mock_title_tool\nAction Input: https://test.com",
        "Thought: taking the hint into account.\nAction: Run_Nikto\nAction Input: https://test.com",
        "Thought: done.\nFinal Answer: complete",
        "Thought: confirmed.\nFinal Answer: complete (confirmed)",
    ])
    graph = _build_custom_workflow(llm, [mock_title_tool, Run_Nikto], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    hint_msgs = [m for m in result["messages"] if "likely vulnerability class" in str(m.content)]
    assert len(hint_msgs) == 1
    assert "File path traversal, simple case" in hint_msgs[0].content
    # 2026-08-01: the directive must name the real live-test tool and must
    # not present Exploit_Suggester as an equivalent way to "test it
    # directly" - see _live_test_directive's docstring for the live-run
    # failure (run bc915491) this locks in the fix for.
    assert "Advanced_Evasion_Probe" in hint_msgs[0].content
    assert "does NOT touch the target" in hint_msgs[0].content
    print("  [PASS] test_vulnerability_hint_in_tool_result_adds_directive_nudge")


def test_matched_vuln_keywords_extracts_raw_keywords():
    """_matched_vuln_keywords is the keyword-matching logic factored out of
    _extract_vulnerability_hints (2026-08-01) so _live_test_directive can
    build a tool-specific instruction from the same matched set."""
    assert _matched_vuln_keywords("Title[File path traversal, simple case]") == ["path traversal"]
    assert _matched_vuln_keywords("classic SQL Injection error") == ["sql injection"]
    assert _matched_vuln_keywords("Host is up. Port 80 open, Apache 2.4.") == []
    assert _matched_vuln_keywords("") == []
    assert _matched_vuln_keywords(None) == []
    print("  [PASS] test_matched_vuln_keywords_extracts_raw_keywords")


def test_live_test_directive_names_advanced_evasion_probe_for_path_traversal():
    """2026-08-01: locks in the fix for the bc915491 live-run failure - the
    directive for path traversal / SQL injection must name
    Advanced_Evasion_Probe specifically and must explicitly rule out
    Exploit_Suggester as a substitute, since Exploit_Suggester only returns
    reference payload text and never touches the target."""
    directive = _live_test_directive(["path traversal"])
    assert "Advanced_Evasion_Probe" in directive
    assert "Exploit_Suggester" in directive
    assert "does NOT touch the target" in directive

    directive_sqli = _live_test_directive(["sql injection"])
    assert "Advanced_Evasion_Probe" in directive_sqli
    print("  [PASS] test_live_test_directive_names_advanced_evasion_probe_for_path_traversal")


def test_live_test_directive_falls_back_for_uncovered_vuln_class():
    """Vulnerability classes with no dedicated live-test tool (e.g.
    cross-site scripting) must still steer toward a real live probe
    (Run_Kali_Command/Run_Nikto/Run_FFUF), not silently say nothing, and
    must not falsely claim Advanced_Evasion_Probe covers them."""
    directive = _live_test_directive(["cross-site scripting"])
    assert "Run_Kali_Command" in directive
    assert "Advanced_Evasion_Probe" not in directive
    print("  [PASS] test_live_test_directive_falls_back_for_uncovered_vuln_class")


def test_already_confirmed_exploitation_detects_evasion_probe_success_marker():
    """Unit coverage for the helper directly: True only for a live-test
    tool (Advanced_Evasion_Probe) whose OWN result carries the evasion
    probe's real success header - not for an unrelated tool, and not for
    a clean/no-finding result from the same tool."""
    success_text = Advanced_Evasion_Probe("https://test.com")
    assert _already_confirmed_exploitation("Advanced_Evasion_Probe", success_text) is True
    assert _already_confirmed_exploitation("Recon_Suite", success_text) is False, \
        "the marker in someone else's tool result must not count"
    assert _already_confirmed_exploitation("Advanced_Evasion_Probe", "No vulnerabilities detected with advanced evasion probes.") is False
    assert _already_confirmed_exploitation("Advanced_Evasion_Probe", "") is False
    assert _already_confirmed_exploitation("Advanced_Evasion_Probe", None) is False
    print("  [PASS] test_already_confirmed_exploitation_detects_evasion_probe_success_marker")


def test_confirmed_exploitation_suppresses_call_it_again_directive():
    """2026-08-23 live-run finding (agent run b4762be3, a PortSwigger
    path-traversal lab): Advanced_Evasion_Probe genuinely confirmed the
    vulnerability and captured real screenshots - but its own success text
    still contains the words "Path Traversal", so the generic keyword
    check re-issued "Call Advanced_Evasion_Probe now" right after the tool
    had just done exactly that, sending the model back to redundantly
    re-run it. This locks in the fix: a confirmed result from the tool
    itself must get a "stop, Final Answer now" nudge instead of the
    generic "go call it" directive."""
    llm = MockLLM([
        "Thought: probe.\nAction: Advanced_Evasion_Probe\nAction Input: https://test.com",
        "Thought: done.\nFinal Answer: confirmed path traversal, evidence captured.",
        "Thought: confirmed, no further scanning applies.\nFinal Answer: confirmed path traversal, evidence captured (again).",
    ])
    graph = _build_custom_workflow(llm, [Advanced_Evasion_Probe], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    already_confirmed_msgs = [m for m in result["messages"] if "already CONFIRMED a real" in str(m.content)]
    assert len(already_confirmed_msgs) == 1
    assert "Advanced_Evasion_Probe" in already_confirmed_msgs[0].content
    assert "Final Answer now" in already_confirmed_msgs[0].content

    # The old, misleading "Call Advanced_Evasion_Probe now against the real
    # target" directive must NOT appear for the tool's own confirmed result.
    call_it_now_msgs = [m for m in result["messages"] if "the only tool that actually sends a live request" in str(m.content)]
    assert len(call_it_now_msgs) == 0
    print("  [PASS] test_confirmed_exploitation_suppresses_call_it_again_directive")


def test_majority_vote_success_tells_model_to_stop_not_just_success():
    """A bare "= SUCCESS" majority-vote note gave the model no reason to
    stop - live runs (b4762be3, 1099dc95) both treated it as encouragement
    to re-run the same already-successful tool "to be sure". The note must
    now explicitly say not to call the tool again and to answer now."""
    llm = ReflectionAwareMockLLM(
        react_responses=[
            "Thought: probe.\nAction: Advanced_Evasion_Probe\nAction Input: https://test.com",
            "Thought: done.\nFinal Answer: confirmed.",
            "Thought: confirmed, no further scanning applies.\nFinal Answer: confirmed (again).",
        ],
        vote_responses=["yes", "yes", "yes"],
    )
    graph = _build_custom_workflow(llm, [Advanced_Evasion_Probe], enable_inter_reflection=True)
    result = graph.invoke(dict(BASE_STATE))

    reflect_msgs = [m for m in result["messages"] if "majority-vote assessment" in str(m.content)]
    assert len(reflect_msgs) == 1
    assert "SUCCESS" in reflect_msgs[0].content
    assert "do not call Advanced_Evasion_Probe again" in reflect_msgs[0].content
    assert "Final Answer now" in reflect_msgs[0].content
    print("  [PASS] test_majority_vote_success_tells_model_to_stop_not_just_success")


def test_give_up_note_surfaces_a_finding_confirmed_earlier_in_the_run():
    """Defense-in-depth for the same failure mode: even if the model
    ignores the "stop, Final Answer now" nudges above and keeps circling
    back (or bounces between already-tried tools) until the loop guard
    gives up, a genuinely confirmed, screenshot-backed finding from
    earlier in the run must not be silently swallowed by the generic
    "partial assessment, no findings" message."""
    llm = MockLLM([
        "Thought: probe.\nAction: Advanced_Evasion_Probe\nAction Input: https://test.com",
        "Thought: probe again to be safe.\nAction: Advanced_Evasion_Probe\nAction Input: https://test.com",
        "Thought: probe a third time.\nAction: Advanced_Evasion_Probe\nAction Input: https://test.com",
        "Thought: probe a fourth time.\nAction: Advanced_Evasion_Probe\nAction Input: https://test.com",
        "Thought: probe a fifth time.\nAction: Advanced_Evasion_Probe\nAction Input: https://test.com",
    ])
    graph = _build_custom_workflow(llm, [Advanced_Evasion_Probe], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    assert result["phase"] == "done"
    give_up_msgs = [m for m in result["messages"] if "stopped early after being blocked" in str(m.content)]
    assert len(give_up_msgs) == 1
    assert "IMPORTANT: despite this early stop, a vulnerability WAS already confirmed" in give_up_msgs[0].content
    print("  [PASS] test_give_up_note_surfaces_a_finding_confirmed_earlier_in_the_run")


def test_give_up_note_stays_generic_when_nothing_was_ever_confirmed():
    """No regression: when the loop guard fires with no confirmed finding
    anywhere in the run (the pre-existing scenario), the give-up message
    must stay exactly the original generic text, with no fabricated
    "vulnerability confirmed" claim added."""
    llm = MockLLM([
        "Thought: probe.\nAction: mock_probe\nAction Input: https://test.com",
        "Thought: probe again to be safe.\nAction: mock_probe\nAction Input: https://test.com",
        "Thought: probe a third time.\nAction: mock_probe\nAction Input: https://test.com",
        "Thought: probe a fourth time.\nAction: mock_probe\nAction Input: https://test.com",
        "Thought: probe a fifth time.\nAction: mock_probe\nAction Input: https://test.com",
    ])
    graph = _build_custom_workflow(llm, [mock_probe], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    give_up_msgs = [m for m in result["messages"] if "stopped early after being blocked" in str(m.content)]
    assert len(give_up_msgs) == 1
    assert "IMPORTANT" not in give_up_msgs[0].content
    print("  [PASS] test_give_up_note_stays_generic_when_nothing_was_ever_confirmed")


def test_final_answer_without_phase56_tool_gets_nudged_once_then_accepted():
    """Rule 5 ("attempt Phase 5/6 before a Final Answer") was advisory text
    only - a live run against scanme.nmap.org concluded after just
    Check_Reachability/Subdomain_Enumeration/Recon_Suite, never touching
    Run_Nikto/Run_FFUF/Exploit_Suggester/Advanced_Evasion_Probe, because
    nothing enforced it. This is a one-time nudge, not a hard block: the
    model gets one chance to reconsider, then its Final Answer is accepted
    even without a Phase 5/6 tool call.

    mock_scan is also not a Phase 1-2 tool, so the first Final Answer now
    absorbs the 2026-07-26 phase12 nudge first, then the phase5/6 nudge,
    before the third is accepted."""
    llm = MockLLM([
        "Thought: scan.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: done already.\nFinal Answer: first attempt",
        "Thought: still nothing else.\nFinal Answer: second attempt",
        "Thought: ok, taking that into account.\nFinal Answer: third attempt",
    ])
    graph = _build_custom_workflow(llm, [mock_scan], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    nudge_msgs = [m for m in result["messages"] if "vulnerability scanning or exploitation" in str(m.content)]
    assert len(nudge_msgs) == 1, "should nudge exactly once, not repeatedly"
    assert result["phase"] == "done"
    assert "third attempt" in result["messages"][-1].content
    print("  [PASS] test_final_answer_without_phase56_tool_gets_nudged_once_then_accepted")


def test_final_answer_with_phase56_tool_is_not_nudged():
    """Verify Final answer with phase56 tool is not nudged.

    Run_Nikto is a Phase 5/6 tool but not a Phase 1-2 tool, so the
    2026-07-26 phase12 nudge still fires once here - the model's identical
    Run_Nikto retry is allowed (the guard's own "twice" tolerance) and the
    2nd Final Answer is then accepted since Run_Nikto already satisfies
    Phase 5/6. The `nudge_msgs` check below is specifically for the
    phase5/6 message text, which correctly never fires."""
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


def test_final_answer_with_zero_tool_calls_gets_nudged_to_investigate_first():
    """2026-07-26 regression: this test used to assert the OPPOSITE (not
    nudged) - that was itself the live bug, hit independently on two real
    runs (a PortSwigger lab, then a real production site,
    cultbeauty.co.uk, a different day): the model wrote "Final Answer:"
    directly inside/after its very first Thought, before ever executing a
    single tool, and the synthesized report that followed contained
    fabricated findings (specific paths, payloads, severities) with zero
    real tool_result backing any of it - a direct Constitution VIII
    ("never fabricate a report") violation this specific check used to
    explicitly declare out of scope. Now nudged exactly once per run
    (mirroring the Phase 5/6 nudge's own one-time design) instead of
    accepted outright."""
    llm = MockLLM([
        "Thought: I already know enough.\nFinal Answer: immediate answer",
        "Thought: fine, taking that into account.\nFinal Answer: immediate answer",
    ])
    graph = _build_custom_workflow(llm, [mock_scan], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    nudge_msgs = [m for m in result["messages"] if "without executing a single tool" in str(m.content)]
    assert len(nudge_msgs) == 1, "should nudge exactly once for a zero-tool-call Final Answer"
    assert result["phase"] == "done"
    print("  [PASS] test_final_answer_with_zero_tool_calls_gets_nudged_to_investigate_first")


def test_zero_tool_call_nudge_is_skipped_once_a_real_tool_executes():
    """After the one-time zero-tool-call nudge, if the model recovers by
    actually calling a tool before its next Final Answer, the zero-tool
    check does not fire again (tried_names is no longer empty) - proving
    the guard only intervenes on a genuinely evidence-free conclusion, not
    every Final Answer forever. mock_scan is also neither a Phase 1-2 nor a
    Phase 5/6 tool, so this also has to absorb the 2026-07-26 phase12
    nudge and the pre-existing phase56 nudge before its "verified" Final
    Answer is finally accepted."""
    llm = MockLLM([
        "Thought: I already know enough.\nFinal Answer: immediate answer",
        "Thought: ok, checking first.\nAction: mock_scan\nAction Input: https://test.com",
        "Thought: now I have real data.\nFinal Answer: verified answer",
        "Thought: still nothing else to add.\nFinal Answer: verified answer (still)",
        "Thought: confirmed, no further scanning applies.\nFinal Answer: verified answer (confirmed)",
    ])
    graph = _build_custom_workflow(llm, [mock_scan], enable_inter_reflection=False)
    result = graph.invoke(dict(BASE_STATE))

    zero_tool_nudges = [m for m in result["messages"] if "without executing a single tool" in str(m.content)]
    assert len(zero_tool_nudges) == 1, "zero-tool-call guard should fire exactly once, not again after a real tool call"
    assert result["phase"] == "done"
    assert "verified answer" in result["messages"][-1].content
    print("  [PASS] test_zero_tool_call_nudge_is_skipped_once_a_real_tool_executes")


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


def test_custom_graph_immediate_final_answer_gets_nudged_first():
    """2026-07-26: an immediate Final Answer with zero tool calls no longer
    ends the run on iteration 1 - see
    test_final_answer_with_zero_tool_calls_gets_nudged_to_investigate_first's
    docstring for the live incident this fixes. MockLLM only has one
    canned response here, so it repeats verbatim on the 2nd attempt - the
    guard only fires once per run (mirroring the Phase 5/6 nudge), so the
    repeated Final Answer is accepted on attempt 2 even though still zero
    real tool calls happened; a model that never calls anything even after
    being told why that's a problem is a separate, broader failure this
    specific check isn't meant to solve alone."""
    llm = MockLLM([
        "Final Answer: Target is clean. No issues found.",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 2, f"Expected 2 (1 nudge + 1 accepted repeat), got {result['iteration_count']}"
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_immediate_final_answer_gets_nudged_first")


def test_custom_graph_no_output_fallback():
    """Verify graph handles empty LLM response.

    mock_scan is neither a Phase 1-2 nor a Phase 5/6 tool, so the first
    Final Answer absorbs the 2026-07-26 phase12 nudge, the second absorbs
    the specs/019 phase5/6 nudge, before the third is accepted."""
    llm = MockLLM([
        "",
        "Thought: Try again.\nAction: mock_scan\nAction Input: test",
        "Final Answer: Done.",
        "Thought: Still nothing else.\nFinal Answer: Done (still).",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))
    assert result["iteration_count"] <= 5, f"Should stop, got {result['iteration_count']}"
    print("  [PASS] test_custom_graph_no_output_fallback")


# -- JSON Action format tests --------------------------

def test_custom_graph_json_action_format():
    """Verify parser handles JSON Action format.

    Neither mock_scan nor mock_search is a Phase 1-2 or Phase 5/6 tool, so
    the first Final Answer absorbs the 2026-07-26 phase12 nudge and the
    second absorbs the specs/019 phase5/6 nudge."""
    llm = MockLLM([
        'Thought: Scanning.\nAction: {"name": "mock_scan", "input": "https://test.com"}\n',
        'Thought: Searching.\nAction: {"name": "mock_search", "input": "nginx 1.24"}\n',
        "Final Answer: Report done.",
        "Thought: Still nothing else.\nFinal Answer: Report done (still).",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Report done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan, mock_search])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 5
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_json_action_format")


def test_custom_graph_json_action_variants():
    """Verify parser accepts alternative JSON key names (action, tool, arguments).

    mock_scan is neither a Phase 1-2 nor a Phase 5/6 tool, so the first
    Final Answer absorbs the 2026-07-26 phase12 nudge and the second
    absorbs the specs/019 phase5/6 nudge."""
    llm = MockLLM([
        'Thought: Scan.\nAction: {"action": "mock_scan", "arguments": "https://test.com"}\n',
        "Final Answer: Done.",
        "Thought: Still nothing else.\nFinal Answer: Done (still).",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 4
    assert result["phase"] == "done"
    print("  [PASS] test_custom_graph_json_action_variants")


def test_custom_graph_malformed_json_fallback_to_text():
    """Verify parser falls back to text format when JSON is malformed.

    mock_scan is neither a Phase 1-2 nor a Phase 5/6 tool, so the first
    Final Answer absorbs the 2026-07-26 phase12 nudge and the second
    absorbs the specs/019 phase5/6 nudge."""
    llm = MockLLM([
        'Thought: Scan.\nAction: {"name": "mock_scan" "input": "missing comma"}\n',  # malformed JSON
        'Thought: Fixed.\nAction: mock_scan\nAction Input: https://test.com',
        "Final Answer: Done.",
        "Thought: Still nothing else.\nFinal Answer: Done (still).",
        "Thought: Confirmed, no further scanning applies.\nFinal Answer: Done (confirmed).",
    ])

    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] <= 5
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
    """Full graph cycle driven by structured decoding instead of free-text output.

    2026-07-26: this Final Answer has zero tool calls behind it, so it now
    absorbs one zero-tool-call nudge first (see
    test_final_answer_with_zero_tool_calls_gets_nudged_to_investigate_first's
    docstring) before being accepted - `StructuredMockLLM` returns the same
    canned action on every call (no cycling), so the repeated Final Answer
    is accepted on the 2nd iteration."""
    llm = StructuredMockLLM(_ArgusAction(thought="Done.", final_answer="Security report here."))
    graph = _build_custom_workflow(llm, [mock_scan])
    result = graph.invoke(dict(BASE_STATE))

    assert result["iteration_count"] == 2
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
# specs/020 (multi-agent role separation, feature-flagged off by default)
# =======================================================
def test_planner_decision_structured_success():
    """Verify Planner decision structured success."""
    llm = StructuredMockLLM(structured_response=_PlannerDecision(
        reasoning="nothing mapped yet", next_role="collector",
    ))
    assert _try_planner_decision(llm, "system text") == "collector"
    print("  [PASS] test_planner_decision_structured_success")


def test_planner_decision_falls_back_when_unsupported():
    """Verify Planner decision falls back when unsupported."""
    llm = MockLLM(["plain text, no with_structured_output"])
    assert _try_planner_decision(llm, "system text") is None
    print("  [PASS] test_planner_decision_falls_back_when_unsupported")


def test_planner_decision_invalid_role_returns_none():
    """Verify Planner decision invalid role returns none."""
    llm = StructuredMockLLM(structured_response=_PlannerDecision(
        reasoning="?", next_role="not_a_real_role",
    ))
    assert _try_planner_decision(llm, "system text") is None
    print("  [PASS] test_planner_decision_invalid_role_returns_none")


def test_multi_role_full_cycle_collector_then_exploiter_then_summarizer():
    """Happy path: planner routes to collector, collector runs one tool,
    planner routes to exploiter, exploiter runs one tool, planner routes to
    summarizer, summarizer produces the final report."""
    llm = MockLLM([
        "I will start with collector to map the attack surface.",
        'Thought: recon.\nAction: {"name": "mock_recon", "input": "https://test.com"}',
        "Recon is done, now send this to the exploiter for vulnerability testing.",
        'Thought: scan.\nAction: {"name": "Run_Nikto", "input": "https://test.com"}',
        "Both steps done, time to summarize.",
        "Final Answer: comprehensive report here",
    ])
    graph = _build_multi_role_workflow(
        llm, {"collector": [mock_recon], "exploiter": [Run_Nikto]},
        enable_inter_reflection=False,
    )
    result = graph.invoke(dict(MULTI_ROLE_BASE_STATE))

    assert result["role_history"] == ["collector", "exploiter", "summarizer"]
    assert result["phase"] == "done"
    assert "comprehensive report here" in result["messages"][-1].content
    # Collector's and Exploiter's tool calls both actually ran (found their
    # way into the Blackboard), not just the routing decisions.
    assert "mock_recon" in result["blackboard_summary"]
    assert "Run_Nikto" in result["blackboard_summary"]
    print("  [PASS] test_multi_role_full_cycle_collector_then_exploiter_then_summarizer")


def test_multi_role_collector_runs_exactly_one_tool_call_per_visit():
    """Verify Multi role collector runs exactly one tool call per visit."""
    llm = MockLLM([
        "collector",
        'Thought: recon.\nAction: {"name": "mock_recon", "input": "https://test.com"}',
        "summarizer",
        "Final Answer: done",
    ])
    graph = _build_multi_role_workflow(
        llm, {"collector": [mock_recon], "exploiter": []},
        enable_inter_reflection=False,
    )
    result = graph.invoke(dict(MULTI_ROLE_BASE_STATE))

    assert len(result["tool_call_history"]) == 1
    assert result["tool_call_history"][0].startswith("mock_recon::")
    print("  [PASS] test_multi_role_collector_runs_exactly_one_tool_call_per_visit")


def test_multi_role_respects_max_iterations():
    """If the Planner keeps bouncing work back and forth without ever
    choosing summarizer, the shared iteration budget still forces
    termination - the same guarantee the single-loop graph gives via
    max_iterations, not something specific to this topology's routing."""
    llm = MockLLM([
        "collector",
        'Thought: recon.\nAction: {"name": "mock_recon", "input": "https://test.com"}',
    ])
    state = dict(MULTI_ROLE_BASE_STATE)
    state["max_iterations"] = 5
    graph = _build_multi_role_workflow(
        llm, {"collector": [mock_recon], "exploiter": []},
        enable_inter_reflection=False,
    )
    result = graph.invoke(state)

    assert result["iteration_count"] <= state["max_iterations"] + 1
    assert result["phase"] == "done", "must still reach summarizer, not hang"
    print(f"  [PASS] test_multi_role_respects_max_iterations (stopped at {result['iteration_count']})")


def test_multi_role_planner_defaults_to_summarizer_on_inconclusive_decision():
    """An inconclusive routing decision (matches none of the 3 expected
    words) ends the run with whatever's known so far rather than spinning
    silently (Constitution VIII) - defaults to summarizer, not a crash."""
    llm = MockLLM([
        "I genuinely cannot decide what to do next.",
        "Final Answer: inconclusive but honest",
    ])
    graph = _build_multi_role_workflow(
        llm, {"collector": [mock_recon], "exploiter": []},
        enable_inter_reflection=False,
    )
    result = graph.invoke(dict(MULTI_ROLE_BASE_STATE))

    assert result["role_history"] == ["summarizer"]
    assert result["phase"] == "done"
    print("  [PASS] test_multi_role_planner_defaults_to_summarizer_on_inconclusive_decision")


def test_multi_role_exploiter_inter_reflection_majority_vote():
    """Inter-reflection (specs/019) is still reachable from the Exploiter
    node - EXPLOITATION_TOOLS are all Exploiter-partitioned tools, so this
    is the only node that can trigger it in this topology."""
    llm = ReflectionAwareMockLLM(
        react_responses=[
            "exploiter",
            'Thought: scan.\nAction: {"name": "Run_Nikto", "input": "https://test.com"}',
            "summarizer",
            "Final Answer: done",
        ],
        vote_responses=["yes", "yes", "no"],
    )
    graph = _build_multi_role_workflow(
        llm, {"collector": [], "exploiter": [Run_Nikto]},
        enable_inter_reflection=True,
    )
    result = graph.invoke(dict(MULTI_ROLE_BASE_STATE))

    reflect_msgs = [m for m in result["messages"] if "majority-vote assessment" in str(m.content)]
    assert len(reflect_msgs) == 1
    assert "SUCCESS" in reflect_msgs[0].content
    print("  [PASS] test_multi_role_exploiter_inter_reflection_majority_vote")


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
    test_extract_vulnerability_hints_detects_title_pattern()
    test_extract_vulnerability_hints_detects_keyword()
    test_extract_vulnerability_hints_no_match_returns_empty()
    test_extract_vulnerability_hints_handles_empty_input()
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
    test_vulnerability_hint_in_tool_result_adds_directive_nudge()
    test_matched_vuln_keywords_extracts_raw_keywords()
    test_live_test_directive_names_advanced_evasion_probe_for_path_traversal()
    test_live_test_directive_falls_back_for_uncovered_vuln_class()
    test_final_answer_without_phase56_tool_gets_nudged_once_then_accepted()
    test_final_answer_with_phase56_tool_is_not_nudged()
    test_final_answer_with_zero_tool_calls_gets_nudged_to_investigate_first()
    test_custom_graph_handles_unknown_tool()
    test_custom_graph_immediate_final_answer_gets_nudged_first()
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
    test_planner_decision_structured_success()
    test_planner_decision_falls_back_when_unsupported()
    test_planner_decision_invalid_role_returns_none()
    test_multi_role_full_cycle_collector_then_exploiter_then_summarizer()
    test_multi_role_collector_runs_exactly_one_tool_call_per_visit()
    test_multi_role_respects_max_iterations()
    test_multi_role_planner_defaults_to_summarizer_on_inconclusive_decision()
    test_multi_role_exploiter_inter_reflection_majority_vote()

    print(f"\n{'='*50}")
    print("ALL TESTS PASSED")
    print(f"{'='*50}")
