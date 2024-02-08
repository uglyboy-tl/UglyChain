from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Storage(ABC):
    @abstractmethod
    def save(self, data: Any) -> None:
        pass

    @abstractmethod
    def load(self, *args, **kwargs) -> Any:
        pass
