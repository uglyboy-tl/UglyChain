#!/usr/bin/env python3

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from loguru import logger

from uglychain.storage import Storage

from .retrieve_with_llm import answer_with_llm, answer_with_map_llm, answer_with_reduce_llm

DEFAULT_N = 5


class BaseRetriever(ABC):
    default_n: int = DEFAULT_N

    @abstractmethod
    def search(self, query: str, n: int) -> List[str]:
        pass

    def get(
        self, query: str, response_mode: Literal["no_text", "compact", "refine", "summary"] = "no_text", n: int = 0
    ) -> str:
        if n == 0:
            n = self.default_n
        context = self.search(query, n)
        if response_mode != "no_text" and context:
            logger.trace(context)
        try:
            if response_mode == "no_text":
                return str(context)
            elif response_mode == "compact":
                return answer_with_llm(query, context)
            elif response_mode == "refine":
                return answer_with_reduce_llm(query, context)
            elif response_mode == "summary":
                return answer_with_map_llm(query, context)
        except Exception:
            return ""


@dataclass
class StorageRetriever(BaseRetriever, ABC):
    start_init: bool = False
    storage: Storage = field(init=False)

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
