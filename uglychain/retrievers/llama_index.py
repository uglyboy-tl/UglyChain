from dataclasses import dataclass, field
from typing import Any, Dict, List, cast

from .base import BaseRetriever


@dataclass
class LlamaIndexRetriever(BaseRetriever):
    index: Any
    query_kwargs: Dict = field(default_factory=dict)

    def __post_init__(self):
        try:
            from llama_index.indices.base import BaseGPTIndex
        except ImportError as err:
            raise ImportError("You need to install `pip install llama-index` to use this retriever.") from err
        self.index = cast(BaseGPTIndex, self.index)

    def search(self, query: str, n: int = BaseRetriever.default_n) -> list[str]:
        query_engine = self.index.as_query_engine(response_mode="no_text", similarity_top_k=n, **self.query_kwargs)
        response = query_engine.query(query)

        # parse source nodes
        docs = []
        for source_node in response.source_nodes:
            docs.append(source_node.text)
        return docs


@dataclass
class LlamaIndexGraphRetriever(BaseRetriever):
    graph: Any
    query_configs: List[Dict] = field(default_factory=list)

    def search(self, query: str, n: int = BaseRetriever.default_n) -> list[str]:
        """Get documents relevant for a query."""
        try:
            from llama_index.composability.graph import (  # type: ignore
                QUERY_CONFIG_TYPE,
                ComposableGraph,
            )
            from llama_index.response.schema import Response  # type: ignore
        except ImportError as err:
            raise ImportError("You need to install `pip install llama-index` to use this retriever.") from err
        graph = cast(ComposableGraph, self.graph)

        # for now, inject response_mode="no_text" into query configs
        for query_config in self.query_configs:
            query_config["response_mode"] = "no_text"
            query_config["similarity_top_k"] = n
        query_configs = cast(List[QUERY_CONFIG_TYPE], self.query_configs)
        response = graph.query(query, query_configs=query_configs)
        response = cast(Response, response)

        # parse source nodes
        docs = []
        for source_node in response.source_nodes:
            docs.append(source_node.text)
        return docs
