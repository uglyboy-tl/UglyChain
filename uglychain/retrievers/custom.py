#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Callable, List

from .base import BaseRetriever


@dataclass
class CustomRetriever(BaseRetriever):
    search_function: Callable[[str, int], List[str]]

    def search(self, query: str, n: int = BaseRetriever.default_n) -> List[str]:
        return self.search_function(query, n)
