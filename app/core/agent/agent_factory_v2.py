# DEPRECATED: This module is deprecated. Use app/core/agent/graph.py instead.
import logging
import warnings
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
    warnings.warn(
        "create_brain is deprecated in favor of build_tactical_graph in app.core.agent.graph",
        DeprecationWarning,
        stacklevel=2
    )
    if registry is None:
        registry = create_default_registry()
    return ArgusBrainV2(registry=registry, model_name=model_name)


def build_tactical_agent():
    """
    Deprecated helper to get the compiled tactical agent graph.
    Use app.core.agent.graph.build_tactical_graph directly.
    """
    warnings.warn(
        "build_tactical_agent is deprecated. Use app.core.agent.graph.build_tactical_graph() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from app.core.agent.graph import build_tactical_graph
    return build_tactical_graph()

