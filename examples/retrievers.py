from loguru import logger

from uglychain.retrievers import get_retriever
from uglychain.retrievers.bm25 import BM25Retriever

def BM25():
    bm25 = BM25Retriever("/tmp/bm25_data.json")
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
    retriever = get_retriever("arxiv")
    query = "quantum computing"
    print(retriever.search(query, 2))

def bing():
    retriever = get_retriever("bing")
    query = "quantum computing"
    print(retriever.search(query, 2))

if __name__ == "__main__":
    #BM25()
    #arxiv()
    bing()