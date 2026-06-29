from abc import ABC, abstractmethod


class BaseTacticalModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    def execute(self, target: str) -> str:
        ...
