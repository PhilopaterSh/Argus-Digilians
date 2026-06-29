import logging
from typing import Any, Optional

from app.core.registry.base_tool import ToolMetadata
from app.core.registry.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ArgusBrainV2:
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        model_name: Optional[str] = None,
    ):
        self.registry = registry if registry is not None else ToolRegistry()
        self.model_name = model_name

    def dispatch(self, tool_name: str, **kwargs) -> Any:
        tool = self.registry.get_tool(tool_name)
        if tool is None:
            raise KeyError(f"Tool not found: {tool_name}")
        logger.info("Dispatching tool: %s", tool_name)
        return tool.execute(**kwargs)

    def get_available_tools(self) -> list[ToolMetadata]:
        return self.registry.list_tools()

    def get_tool_names(self) -> list[str]:
        return self.registry.get_tool_names()
