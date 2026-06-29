from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolMetadata:
    name: str
    description: str
    version: str = "1.0.0"


class BaseToolService(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        ...

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        ...
