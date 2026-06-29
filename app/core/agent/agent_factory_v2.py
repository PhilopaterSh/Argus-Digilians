import logging
from typing import Optional

from app.core.registry.tool_registry import ToolRegistry
from app.core.agent.brain_v2 import ArgusBrainV2

logger = logging.getLogger(__name__)


def register_all_tools(registry: ToolRegistry) -> None:
    from app.tools.tool_registry import WSLBridgeTools

    facade = WSLBridgeTools()
    for meta in facade.registry.list_tools():
        tool = facade.registry.get_tool(meta.name)
        if tool:
            registry.register(tool)
    logger.info("Registered %d tools via factory", len(registry))


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_all_tools(registry)
    return registry


def create_brain(
    registry: Optional[ToolRegistry] = None,
    model_name: Optional[str] = None,
) -> ArgusBrainV2:
    if registry is None:
        registry = create_default_registry()
    return ArgusBrainV2(registry=registry, model_name=model_name)
