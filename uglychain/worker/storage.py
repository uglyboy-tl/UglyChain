from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Storage(ABC):
    @abstractmethod
    def save(self, data):
        pass

    @abstractmethod
    def load(self):
        pass
