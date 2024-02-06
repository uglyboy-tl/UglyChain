#!/usr/bin/env python3

from .arxiv import ArxivRetriever
from .base import BaseRetriever, StoresRetriever
from .bing import BingRetriever
from .llama_index import LlamaIndexGraphRetriever, LlamaIndexRetriever
from .open_procedures import OpenProceduresRetriever

try:
    from .bm25 import BM25Retriever
except ImportError:
    BM25Retriever = None

RETRIEVERS = {
    "bing": BingRetriever,
    "arxiv": ArxivRetriever,
    "open_procedures": OpenProceduresRetriever,
    "llama_index": LlamaIndexRetriever,
    "llama_index_graph": LlamaIndexGraphRetriever,
}

STORE_RETRIEVERS = {"bm25": BM25Retriever}


def get_retriever(retriever_name: str = "combine") -> BaseRetriever:
    if retriever_name in RETRIEVERS.keys():
        retriever = RETRIEVERS[retriever_name]
        if retriever is None:
            raise NotImplementedError(f"{retriever_name} Retriever not installed")
        else:
            return retriever()
    else:
        raise NotImplementedError(f"{retriever_name} Retriever not implemented")


def get_stores_retriever(retriever_name: str = "bm25", path: str = "", start_int: bool = False) -> StoresRetriever:
    if retriever_name in STORE_RETRIEVERS.keys():
        retriever = STORE_RETRIEVERS[retriever_name]
        if retriever is None:
            raise NotImplementedError(f"{retriever_name} StoresRetriever not installed")
        else:
            return retriever(path, start_int)
    else:
        raise NotImplementedError(f"{retriever_name} StoresRetriever not implemented")


__all__ = ["BaseRetriever", "StoresRetriever", "get_retriever", "get_stores_retriever"]
