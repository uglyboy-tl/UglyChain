from loguru import logger

from uglychain.retrievers import Retriever
from uglychain.storage import DillStorage


def BM25():
    storage = DillStorage("data/test.pkl")
    bm25 = Retriever.BM25.getStorage(storage)
    query = "天安门"
    logger.info(bm25.search(query, 2))
    bm25.init()
    logger.info(bm25.search(query, 2))
    bm25.add("我爱北京天安门")
    bm25.add("天安门上太阳升")
    bm25.add("伟大领袖毛主席")
    bm25.add("指引我们向前进")
    logger.info(bm25.search(query, 2))


def arxiv():
    retriever = Retriever.Arxiv()
    query = "quantum computing"
    logger.info(retriever.get(query, "refine"))


def bing():
    retriever = Retriever.Bing()
    query = "量子计算是什么？"
    logger.info(retriever.get(query, "summary"))


if __name__ == "__main__":
    # BM25()
    # arxiv()
    bing()
