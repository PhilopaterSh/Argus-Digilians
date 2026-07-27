from abc import ABC, abstractmethod


class BaseTacticalModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Description."""
        ...

    @abstractmethod
    def execute(self, target: str) -> str:
        """Execute."""
        ...
