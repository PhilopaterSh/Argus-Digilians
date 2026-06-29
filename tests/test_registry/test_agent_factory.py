from app.core.agent.agent_factory_v2 import create_default_registry, create_brain


def test_create_default_registry_returns_registry():
    registry = create_default_registry()
    assert len(registry) > 0


def test_create_brain_returns_brain():
    brain = create_brain()
    assert brain is not None
    assert brain.registry is not None


def test_create_brain_with_custom_registry():
    from app.core.registry.tool_registry import ToolRegistry
    custom = ToolRegistry()
    brain = create_brain(registry=custom)
    assert brain.registry is custom
