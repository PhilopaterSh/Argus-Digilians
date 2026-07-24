"""Unit tests for the consolidated ArgusBrain (app.core.agent.brain).

Covers the tool-dispatch surface that used to live on the deprecated
ArgusBrainV2 (app.core.agent.brain_v2, removed per specs/012 T026).
"""
import pytest
from langchain_core.tools import Tool

from app.core.agent.brain import ArgusBrain


def _make_brain():
    """Build an ArgusBrain with one fake tool and RAG disabled, for tool-dispatch tests.

    Returns:
        ArgusBrain: Configured with a single "fake" tool.
    """
    def fake_func(x: str = "") -> str:
        """Fake func."""
        return f"executed:{x}"

    tool = Tool(name="fake", description="A fake tool", func=fake_func)
    return ArgusBrain("test-model", [tool], rag_config={"enabled": False})


def test_dispatch_calls_tool_func():
    """Verify Dispatch calls tool func."""
    brain = _make_brain()
    result = brain.dispatch("fake", x="hello")
    assert result == "executed:hello"


def test_dispatch_unknown_tool_raises():
    """Verify Dispatch unknown tool raises."""
    brain = _make_brain()
    with pytest.raises(KeyError, match="Tool not found: unknown"):
        brain.dispatch("unknown")


def test_get_available_tools():
    """Verify Get available tools."""
    brain = _make_brain()
    tools = brain.get_available_tools()
    assert len(tools) == 1
    assert tools[0].name == "fake"


def test_get_tool_names():
    """Verify Get tool names."""
    brain = _make_brain()
    assert brain.get_tool_names() == ["fake"]


def test_no_tools_on_init():
    """Verify No tools on init."""
    brain = ArgusBrain("test-model", [], rag_config={"enabled": False})
    assert brain.get_tool_names() == []
