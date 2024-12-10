#!/usr/bin/env python3
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .base import BaseRetriever


@dataclass
class CustomRetriever(BaseRetriever):
    search_function: Callable[[str, int], list[str]]

    def search(self, query: str, n: int = BaseRetriever.default_n) -> list[str]:
        return self.search_function(query, n)
