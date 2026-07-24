"""Generic tool registry data structure.

Note the sibling `app/tools/tool_registry.py` - same basename, different
module: this file defines the `ToolRegistry` class itself; that one is
`WSLBridgeTools`, a facade that imports every concrete tool service and
registers instances into a `ToolRegistry` it owns. If disambiguating by
basename alone, check the full import path.
"""
import logging
from typing import Optional

from app.core.registry.base_tool import BaseToolService, ToolMetadata

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        """Init  ."""
        self._tools: dict[str, BaseToolService] = {}

    def register(self, tool: BaseToolService) -> None:
        """Register a tool by its `metadata.name`, warning (not failing) on overwrite.

        Args:
            tool (BaseToolService): The tool instance to register.

        Returns:
            None

        Raises:
            TypeError: If `tool` isn't a `BaseToolService` instance.
        """
        if not isinstance(tool, BaseToolService):
            raise TypeError(f"Expected BaseToolService, got {type(tool).__name__}")
        name = tool.metadata.name
        if name in self._tools:
            logger.warning("Overwriting existing tool: %s", name)
        self._tools[name] = tool
        logger.info("Registered tool: %s v%s", name, tool.metadata.version)

    def unregister(self, name: str) -> None:
        """Unregister."""
        if name in self._tools:
            del self._tools[name]
            logger.info("Unregistered tool: %s", name)

    def get_tool(self, name: str) -> Optional[BaseToolService]:
        """Get tool."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolMetadata]:
        """List tools."""
        return [t.metadata for t in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        """Get tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        """Len  ."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Contains  ."""
        return name in self._tools
