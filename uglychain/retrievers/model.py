from enum import Enum

from uglychain.storage import Storage

from .arxiv import ArxivRetriever
from .base import BaseRetriever, StorageRetriever
from .bing import BingRetriever
from .bm25 import BM25Retriever
from .custom import CustomRetriever
from .llama_index import LlamaIndexRetriever


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

    def getStorage(self, storage: Storage, **kwargs) -> StorageRetriever:
        retriever = self(storage=storage, **kwargs)
        if not isinstance(retriever, StorageRetriever):
            raise TypeError(f"{self.name} is not a StoresRetriever")
        return retriever
