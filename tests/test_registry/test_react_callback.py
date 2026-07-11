"""Unit tests for app/core/agent/react_callback.py::LiveFeedCallbackHandler (specs/017).

Verifies each LangChain callback hook appends a correctly-shaped event via
the existing app/core/agent/contracts.py::append_run_event contract - the
same one app/GUI/tabs/agent.py's "Agent Feed" already polls and renders.
"""
import json
import os
import uuid

import pytest
from langchain_core.agents import AgentAction, AgentFinish

from app.core.agent.react_callback import ConsoleTraceCallbackHandler, LiveFeedCallbackHandler


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / "state.json")


def _events(state_file):
    with open(state_file, encoding="utf-8") as f:
        return json.load(f)["events"]


def test_on_agent_action_appends_running_event_with_thought_and_input(state_file):
    handler = LiveFeedCallbackHandler(state_file, "run-1", "example.com", "production")
    action = AgentAction(tool="Run_Nikto", tool_input="http://example.com", log="Thought: scan it.\nAction: Run_Nikto")

    handler.on_agent_action(action, run_id=uuid.uuid4())

    events = _events(state_file)
    assert len(events) == 1
    assert events[0]["status"] == "running"
    assert events[0]["node"] == "agent"
    assert "Thought: scan it." in events[0]["detail"]
    assert "http://example.com" in events[0]["detail"]
    assert events[0]["run_id"] == "run-1"
    assert events[0]["target"] == "example.com"
    assert events[0]["mode"] == "production"


def test_on_tool_end_appends_completed_observation_event(state_file):
    handler = LiveFeedCallbackHandler(state_file, "run-1", "example.com", "production")

    handler.on_tool_end("nikto found 3 issues", run_id=uuid.uuid4())

    events = _events(state_file)
    assert events[0]["status"] == "completed"
    assert "Observation: nikto found 3 issues" in events[0]["detail"]


def test_on_tool_error_appends_failed_event_not_a_fabricated_success(state_file):
    handler = LiveFeedCallbackHandler(state_file, "run-1", "example.com", "production")

    handler.on_tool_error(RuntimeError("boom"), run_id=uuid.uuid4())

    events = _events(state_file)
    assert events[0]["status"] == "failed"
    assert "boom" in events[0]["detail"]


def test_on_agent_finish_appends_completed_event(state_file):
    handler = LiveFeedCallbackHandler(state_file, "run-1", "example.com", "production")
    finish = AgentFinish(return_values={"output": "done"}, log="Final Answer: done")

    handler.on_agent_finish(finish, run_id=uuid.uuid4())

    events = _events(state_file)
    assert events[0]["status"] == "completed"
    assert "final security report" in events[0]["detail"].lower()


def test_multiple_steps_accumulate_in_order(state_file):
    handler = LiveFeedCallbackHandler(state_file, "run-1", "example.com", "production")
    handler.on_agent_action(AgentAction(tool="A", tool_input="x", log="Thought: a"), run_id=uuid.uuid4())
    handler.on_tool_end("obs-a", run_id=uuid.uuid4())
    handler.on_agent_action(AgentAction(tool="B", tool_input="y", log="Thought: b"), run_id=uuid.uuid4())
    handler.on_tool_end("obs-b", run_id=uuid.uuid4())

    events = _events(state_file)
    assert len(events) == 4
    assert [e["status"] for e in events] == ["running", "completed", "running", "completed"]


def test_long_detail_is_truncated(state_file):
    handler = LiveFeedCallbackHandler(state_file, "run-1", "example.com", "production")

    handler.on_tool_end("x" * 5000, run_id=uuid.uuid4())

    events = _events(state_file)
    assert len(events[0]["detail"]) == 500  # _TRUNCATE_CHARS cap in react_callback.py


def test_on_graph_event_appends_event_with_given_status(state_file):
    """specs/018: drives the live feed from a raw LangGraph StateGraph.stream()
    loop (app/core/agent/brain.py::_run_structured_graph), which never fires
    the AgentExecutor-specific hooks above."""
    handler = LiveFeedCallbackHandler(state_file, "run-1", "example.com", "production")

    handler.on_graph_event("running", "Thought: about to scan.")
    handler.on_graph_event("completed", "Observation: scan finished.")

    events = _events(state_file)
    assert len(events) == 2
    assert events[0]["status"] == "running"
    assert "Thought: about to scan." in events[0]["detail"]
    assert events[1]["status"] == "completed"
    assert "Observation: scan finished." in events[1]["detail"]


class TestConsoleTraceCallbackHandler:
    """Added 2026-07-10: user asked for the CLI to show the model's
    reasoning in as much detail as possible - scripts/run_argus_cli.py
    previously passed no callbacks to brain.ask() at all."""

    def test_reasoning_step_prints_numbered_step_header(self, capsys):
        handler = ConsoleTraceCallbackHandler()
        handler.on_graph_event("running", "Thought: check reachability.\nAction: Check_Reachability")

        out = capsys.readouterr().out
        assert "STEP 1" in out
        assert "Thought: check reachability." in out

    def test_step_counter_increments_across_reasoning_steps_only(self, capsys):
        handler = ConsoleTraceCallbackHandler()
        handler.on_graph_event("running", "Thought: first.\nAction: A")
        handler.on_graph_event("completed", "Observation: result of A")
        handler.on_graph_event("running", "Thought: second.\nAction: B")

        out = capsys.readouterr().out
        assert "STEP 1" in out
        assert "STEP 2" in out
        assert "STEP 3" not in out  # the Observation must not consume a step number

    def test_observation_prints_as_tool_result_not_a_numbered_step(self, capsys):
        handler = ConsoleTraceCallbackHandler()
        handler.on_graph_event("completed", "Observation: Nikto found 3 issues")

        out = capsys.readouterr().out
        assert "[TOOL RESULT]" in out
        assert "Nikto found 3 issues" in out
        assert "STEP" not in out

    def test_reflection_prints_as_reflection_not_a_numbered_step(self, capsys):
        handler = ConsoleTraceCallbackHandler()
        handler.on_graph_event("reflecting", "Reflection: majority-vote assessment of Run_Nikto result = SUCCESS.")

        out = capsys.readouterr().out
        assert "[REFLECTION]" in out
        assert "SUCCESS" in out
        assert "STEP" not in out
