from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

from uglychain.storage import LlamaIndexStorage
from uglychain.utils import config

from .base import BaseRetriever, StorageRetriever

try:
    from llama_index.core import Settings
    from llama_index.embeddings.openai import OpenAIEmbedding

    Settings.embed_model = OpenAIEmbedding(
        api_base=config.embedding_api_base, api_key=config.embedding_api_key, model=config.embedding_model
    )
except Exception:
    pass


@dataclass
class LlamaIndexRetriever(BaseRetriever):
    index: Any = None
    query_kwargs: Dict = field(default_factory=dict)

    def __post_init__(self):
        assert self.index is not None, "You need to set `index` to use this retriever."
        try:
            from llama_index.core.indices.base import BaseGPTIndex
        except ImportError as err:
            raise ImportError(
                "You need to install `pip install llama-index-core llama-index-embeddings-openai` to use this retriever."
            ) from err
        self.index = cast(BaseGPTIndex, self.index)

    def search(self, query: str, n: int = BaseRetriever.default_n) -> List[str]:
        retriever = self.index.as_retriever(similarity_top_k=n, **self.query_kwargs)
        response = retriever.retrieve(query)

        # parse source nodes
        docs = []
        for source_node in response:
            docs.append(source_node.text)
        return docs


@dataclass
class LlamaIndexStorageRetriever(LlamaIndexRetriever, StorageRetriever):
    persist_dir: str = ""
    storage: LlamaIndexStorage = field(default_factory=LlamaIndexStorage)

    def __post_init__(self):
        if self.persist_dir:
            self.storage = LlamaIndexStorage(persist_dir=self.persist_dir)
        StorageRetriever.__post_init__(self)

    def init(self):
        try:
            from llama_index.core import VectorStoreIndex
        except ImportError as err:
            raise ImportError("You need to install `pip install llama-index-core` to use this retriever.") from err
        self.index = VectorStoreIndex.from_documents([])
        self.storage.save(self.index)

    def add(self, text: str, metadata: Optional[Dict[str, str]] = None):
        if not metadata:
            metadata = {}
        try:
            from llama_index.core import Document
        except ImportError as err:
            raise ImportError("You need to install `pip install llama-index-core` to use this retriever.") from err
        self.index.insert(Document(text=text, extra_info=metadata))
        self.storage.save(self.index)

    def _load(self):
        try:
            self.index = self.storage.load()
        except Exception:
            self.init()
