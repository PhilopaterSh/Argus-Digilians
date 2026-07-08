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

from app.core.agent.react_callback import LiveFeedCallbackHandler


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
