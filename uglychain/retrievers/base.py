#!/usr/bin/env python3

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

DEFAULT_N = 5


class BaseRetriever(ABC):
    default_n: int = DEFAULT_N

    @abstractmethod
    def search(self, query: str, n: int) -> List[str]:
        pass

    def get(self, query: str) -> str:
        try:
            return self.search(query, 1)[0]
        except Exception:
            return ""


@dataclass
class StoresRetriever(BaseRetriever, ABC):
    path: str
    start_init: bool = False

    def __post_init__(self):
        if self.start_init:
            self.init()
        else:
            self._load()

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def add(self, text: str, metadata: Optional[Dict[str, str]] = None):
        pass

    def _load(self):
        self.init()

    def all(self) -> List[str]:
        return []
