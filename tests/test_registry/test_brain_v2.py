import pytest
from app.core.agent.brain_v2 import ArgusBrainV2
from app.core.registry.tool_registry import ToolRegistry
from app.core.registry.base_tool import BaseToolService, ToolMetadata


class FakeTool(BaseToolService):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(name="fake", description="A fake tool")

    def execute(self, **kwargs):
        return f"executed:{kwargs.get('x', '')}"


def _make_brain():
    r = ToolRegistry()
    r.register(FakeTool())
    return ArgusBrainV2(registry=r)


def test_dispatch_calls_execute():
    brain = _make_brain()
    result = brain.dispatch("fake", x="hello")
    assert result == "executed:hello"


def test_dispatch_unknown_tool_raises():
    brain = _make_brain()
    with pytest.raises(KeyError, match="Tool not found: unknown"):
        brain.dispatch("unknown")


def test_get_available_tools():
    brain = _make_brain()
    tools = brain.get_available_tools()
    assert len(tools) == 1
    assert tools[0].name == "fake"


def test_get_tool_names():
    brain = _make_brain()
    names = brain.get_tool_names()
    assert "fake" in names


def test_default_registry_on_init():
    brain = ArgusBrainV2()
    assert len(brain.registry) == 0
