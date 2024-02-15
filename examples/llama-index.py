from loguru import logger

from uglychain.retrievers import Retriever
from uglychain.retrievers.llama_index import LlamaIndexStorageRetriever

LlamaIndexStorageRetriever()

def load_index():
    retriever = Retriever.LlamaIndex.getStorage(persist_dir="./data/storage")
    out = retriever.get("组织共情是什么？")
    logger.info(out)


def llama_index():
    llama_index = Retriever.LlamaIndex.getStorage(True)
    query = "天安门"
    logger.info(llama_index.search(query, 2))
    llama_index.init()
    logger.info(llama_index.search(query, 2))
    llama_index.add("我爱北京天安门")
    llama_index.add("天安门上太阳升")
    llama_index.add("伟大领袖毛主席")
    llama_index.add("指引我们向前进")
    logger.info(llama_index.search(query, 2))


if __name__ == "__main__":
    # load_index()
    llama_index()
