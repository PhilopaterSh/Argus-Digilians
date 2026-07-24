import pytest
from app.core.registry.base_tool import BaseToolService, ToolMetadata

pytestmark = pytest.mark.unit


class ConcreteTool(BaseToolService):
    @property
    def metadata(self) -> ToolMetadata:
        """Metadata."""
        return ToolMetadata(name="test_tool", description="A test tool")

    def execute(self, **kwargs):
        """Execute."""
        return f"executed: {kwargs.get('arg', 'none')}"


def test_abc_cannot_be_instantiated():
    """Verify Abc cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseToolService()


def test_concrete_tool_metadata():
    """Verify Concrete tool metadata."""
    tool = ConcreteTool()
    assert tool.metadata.name == "test_tool"
    assert tool.metadata.description == "A test tool"


def test_concrete_tool_execute():
    """Verify Concrete tool execute."""
    tool = ConcreteTool()
    result = tool.execute(arg="hello")
    assert result == "executed: hello"


def test_concrete_tool_execute_default():
    """Verify Concrete tool execute default."""
    tool = ConcreteTool()
    result = tool.execute()
    assert result == "executed: none"


def test_tool_metadata_default_version():
    """Verify Tool metadata default version."""
    meta = ToolMetadata(name="x", description="y")
    assert meta.version == "1.0.0"
