"""Unit tests for the canonical agent factory (app.core.agent.agent_factory).

Replaces the tests that used to exercise the deprecated
app.core.agent.agent_factory_v2 shims (removed per specs/012 T027).
"""
from langchain_classic.agents import AgentExecutor
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.tools import Tool

import pytest

from app.core.agent.agent_factory import build_agent_executor
from app.core.prompts import get_argus_prompt

pytestmark = pytest.mark.unit


def _make_tools():
    """Make tools."""
    return [Tool(name="fake", description="A fake tool", func=lambda x="": f"executed:{x}")]


def test_build_agent_executor_returns_agent_executor():
    """Verify Build agent executor returns agent executor."""
    llm = FakeListLLM(responses=["Final Answer: done"])
    executor = build_agent_executor(llm=llm, tools=_make_tools(), prompt=get_argus_prompt())
    assert isinstance(executor, AgentExecutor)
    assert executor.tools[0].name == "fake"


def test_build_agent_executor_respects_max_iterations():
    """Verify Build agent executor respects max iterations."""
    llm = FakeListLLM(responses=["Final Answer: done"])
    executor = build_agent_executor(
        llm=llm, tools=_make_tools(), prompt=get_argus_prompt(), max_iterations=5
    )
    assert executor.max_iterations == 5


def test_build_agent_executor_handles_parsing_errors():
    """Verify Build agent executor handles parsing errors."""
    llm = FakeListLLM(responses=["Final Answer: done"])
    executor = build_agent_executor(llm=llm, tools=_make_tools(), prompt=get_argus_prompt())
    assert executor.handle_parsing_errors is True
