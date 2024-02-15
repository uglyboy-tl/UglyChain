from dataclasses import dataclass, field
from typing import Any, Dict

from .base import Storage


@dataclass
class LlamaIndexStorage(Storage):
    persist_dir: str = "data/llama-index"
    kwargs: Dict = field(default_factory=dict)

    def save(self, index: Any):
        if self.kwargs:
            index.storage_context.persist(**self.kwargs)
        else:
            index.storage_context.persist(persist_dir=self.persist_dir)

    def load(self) -> Any:
        try:
            from llama_index.core import (
                StorageContext,
                load_index_from_storage,
            )
        except ImportError as err:
            raise ImportError("You need to install `pip install llama-index-core` to use this storage.") from err
        if self.kwargs:
            storage_context = StorageContext.from_defaults(**self.kwargs)
        else:
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
        index = load_index_from_storage(storage_context)
        return index
