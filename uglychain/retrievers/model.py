from enum import Enum

from .arxiv import ArxivRetriever
from .base import BaseRetriever, StorageRetriever
from .bing import BingRetriever
from .bm25 import BM25Retriever
from .custom import CustomRetriever
from .llama_index import LlamaIndexRetriever, LlamaIndexStorageRetriever


class Retriever(Enum):
    Bing = BingRetriever
    Arxiv = ArxivRetriever
    LlamaIndex = LlamaIndexRetriever
    BM25 = BM25Retriever
    Combine = "CombineRetriever"
    Custom = CustomRetriever

    def __call__(self, *args, **kwargs) -> BaseRetriever:
        if self.name == "Combine":
            from .combine import CombineRetriever

            return CombineRetriever(*args, **kwargs)
        return self.value(*args, **kwargs)  # type: ignore

    def getStorage(self, *args, **kwargs) -> StorageRetriever:
        if self.name == "LlamaIndex":
            retriever = LlamaIndexStorageRetriever(*args, **kwargs)
        else:
            retriever = self(*args, **kwargs)
        if not isinstance(retriever, StorageRetriever):
            raise TypeError(f"{self.name} is not a StoresRetriever")
        return retriever
