import logging
from typing import Optional

from app.core.registry.base_tool import BaseToolService, ToolMetadata

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseToolService] = {}

    def register(self, tool: BaseToolService) -> None:
        if not isinstance(tool, BaseToolService):
            raise TypeError(f"Expected BaseToolService, got {type(tool).__name__}")
        name = tool.metadata.name
        if name in self._tools:
            logger.warning("Overwriting existing tool: %s", name)
        self._tools[name] = tool
        logger.info("Registered tool: %s v%s", name, tool.metadata.version)

    def unregister(self, name: str) -> None:
        if name in self._tools:
            del self._tools[name]
            logger.info("Unregistered tool: %s", name)

    def get_tool(self, name: str) -> Optional[BaseToolService]:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolMetadata]:
        return [t.metadata for t in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
