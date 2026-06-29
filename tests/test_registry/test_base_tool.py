import pytest
from app.core.registry.base_tool import BaseToolService, ToolMetadata


class ConcreteTool(BaseToolService):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(name="test_tool", description="A test tool")

    def execute(self, **kwargs):
        return f"executed: {kwargs.get('arg', 'none')}"


def test_abc_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseToolService()


def test_concrete_tool_metadata():
    tool = ConcreteTool()
    assert tool.metadata.name == "test_tool"
    assert tool.metadata.description == "A test tool"


def test_concrete_tool_execute():
    tool = ConcreteTool()
    result = tool.execute(arg="hello")
    assert result == "executed: hello"


def test_concrete_tool_execute_default():
    tool = ConcreteTool()
    result = tool.execute()
    assert result == "executed: none"


def test_tool_metadata_default_version():
    meta = ToolMetadata(name="x", description="y")
    assert meta.version == "1.0.0"
