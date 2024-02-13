from dataclasses import dataclass, field
from typing import Any, Dict, List, cast

from .base import BaseRetriever


@dataclass
class LlamaIndexRetriever(BaseRetriever):
    index: Any
    query_kwargs: Dict = field(default_factory=dict)

    def __post_init__(self):
        try:
            from llama_index.core.indices.base import BaseGPTIndex
        except ImportError as err:
            raise ImportError("You need to install `pip install llama-index` to use this retriever.") from err
        self.index = cast(BaseGPTIndex, self.index)

    def search(self, query: str, n: int = BaseRetriever.default_n) -> List[str]:
        retriever = self.index.as_retriever(similarity_top_k=n, **self.query_kwargs)
        response = retriever.retrieve(query)

        # parse source nodes
        docs = []
        for source_node in response:
            docs.append(source_node.text)
        return docs
