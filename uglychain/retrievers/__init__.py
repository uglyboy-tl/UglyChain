#!/usr/bin/env python3
from enum import Enum

from uglychain.storage import Storage

from .arxiv import ArxivRetriever
from .base import BaseRetriever, StorageRetriever
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

    def __call__(self, *args, **kwargs) -> BaseRetriever:
        return self.value(*args, **kwargs)

    def getStorage(self, storage: Storage, **kwargs) -> StorageRetriever:
        retriever = self(storage=storage, **kwargs)
        if not isinstance(retriever, StorageRetriever):
            raise TypeError(f"{self.name} is not a StoresRetriever")
        return retriever


__all__ = ["Retriever", "BaseRetriever", "StorageRetriever"]
