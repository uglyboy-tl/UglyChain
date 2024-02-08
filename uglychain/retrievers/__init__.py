#!/usr/bin/env python3
from enum import Enum
from typing import Union

from .arxiv import ArxivRetriever
from .base import BaseRetriever, StoresRetriever
from .bing import BingRetriever
from .bm25 import BM25Retriever
from .llama_index import LlamaIndexGraphRetriever, LlamaIndexRetriever
from .open_procedures import OpenProceduresRetriever


class Retriever(Enum):
    Bing = BingRetriever
    Arxiv = ArxivRetriever
    OpenProcedures = OpenProceduresRetriever
    LlamaIndex = LlamaIndexRetriever
    LLamaIndexGraph = LlamaIndexGraphRetriever
    BM25 = BM25Retriever

    def __call__(self, *args, **kwargs) -> Union[BaseRetriever, StoresRetriever]:
        return self.value(*args, **kwargs)


__all__ = ["Retriever", "BaseRetriever", "StoresRetriever"]
