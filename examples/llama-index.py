from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from loguru import logger

from uglychain.retrievers import LlamaIndexRetriever
from uglychain.utils import config

embed_model = OpenAIEmbedding(
    api_base="https://api.01ww.xyz/v1", api_key=config.yi_api_key, model="text-embedding-ada-002"
)
Settings.embed_model = embed_model

# check if storage already exists
PERSIST_DIR = "./data/storage"
# load the existing index
storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
index = load_index_from_storage(storage_context)

retriever = LlamaIndexRetriever(index)

out = retriever.search("共情是什么？", 5)
logger.info(len(out))
logger.info(out)
