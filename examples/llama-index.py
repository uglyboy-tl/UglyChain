import logging
import os
import sys

from llama_index import (
    ServiceContext,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
    set_global_service_context,
)
from llama_index.embeddings import OpenAIEmbedding

from uglychain.retrievers import LlamaIndexRetriever
from uglychain.utils import config

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

embed_model = OpenAIEmbedding(
    api_base="https://api.01ww.xyz/v1", api_key=config.yi_api_key, model="text-embedding-ada-002"
)
service_context = ServiceContext.from_defaults(embed_model=embed_model)
set_global_service_context(service_context)

# check if storage already exists
PERSIST_DIR = "./data/storage"
if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)


retriever = LlamaIndexRetriever(index)

docs = retriever.get("共情是什么？")
print(docs)
