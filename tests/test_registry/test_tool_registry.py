import pytest
from app.core.registry.tool_registry import ToolRegistry
from app.core.registry.base_tool import BaseToolService, ToolMetadata


class FakeTool(BaseToolService):
    @property
    def metadata(self) -> ToolMetadata:
        """Metadata."""
        return ToolMetadata(name="fake", description="Fake tool for testing")

    def execute(self, **kwargs):
        """Execute."""
        return "done"


class AnotherTool(BaseToolService):
    @property
    def metadata(self) -> ToolMetadata:
        """Metadata."""
        return ToolMetadata(name="another", description="Another test tool")

    def execute(self, **kwargs):
        """Execute."""
        return "also done"


def _make_registry():
    r = ToolRegistry()
    r.register(FakeTool())
    r.register(AnotherTool())
    return r


def test_register_and_get():
    """Verify Register and get."""
    r = ToolRegistry()
    t = FakeTool()
    r.register(t)
    assert r.get_tool("fake") is t


def test_get_nonexistent_returns_none():
    """Verify Get nonexistent returns none."""
    r = ToolRegistry()
    assert r.get_tool("nonexistent") is None


def test_unregister():
    """Verify Unregister."""
    r = _make_registry()
    assert "fake" in r
    r.unregister("fake")
    assert "fake" not in r


def test_unregister_nonexistent_is_safe():
    """Verify Unregister nonexistent is safe."""
    r = ToolRegistry()
    r.unregister("nothing")  # should not raise


def test_list_tools():
    """Verify List tools."""
    r = _make_registry()
    names = [m.name for m in r.list_tools()]
    assert "fake" in names
    assert "another" in names


def test_get_tool_names():
    """Verify Get tool names."""
    r = _make_registry()
    names = r.get_tool_names()
    assert "fake" in names
    assert "another" in names


def test_len():
    """Verify Len."""
    r = _make_registry()
    assert len(r) == 2
    r.unregister("fake")
    assert len(r) == 1


def test_contains():
    """Verify Contains."""
    r = _make_registry()
    assert "fake" in r
    assert "nothing" not in r


def test_register_raises_type_error():
    """Verify Register raises type error."""
    r = ToolRegistry()
    with pytest.raises(TypeError):
        r.register("not a tool")  # type: ignore


def test_register_duplicate_warns(caplog):
    """Verify Register duplicate warns.
    
    Args:
        caplog: pytest fixture (see the module's @pytest.fixture definitions).
    """
    r = ToolRegistry()
    r.register(FakeTool())
    r.register(FakeTool())
    assert "Overwriting existing tool: fake" in caplog.text
