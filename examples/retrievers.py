from typing import List

import requests
from loguru import logger

from uglychain import Model
from uglychain.retrievers import Retriever
from uglychain.storage import DillStorage


def BM25():
    bm25 = Retriever.BM25.getStorage(storage=DillStorage("data/test.pkl"))
    query = "天安门"
    logger.info(bm25.search(query, 2))
    bm25.init()
    logger.info(bm25.search(query, 2))
    bm25.add("我爱北京天安门")
    bm25.add("天安门上太阳升")
    bm25.add("伟大领袖毛主席")
    bm25.add("指引我们向前进")
    logger.info(bm25.search(query, 2))


def bing():
    retriever = Retriever.Bing()
    query = "量子计算是什么？"
    logger.info(retriever.get(query, "summary"))


def combine():
    retriever = Retriever.Combine([Retriever.Arxiv, Retriever.Bing], Model.GPT3_TURBO)
    query = "大语言模型在 Agent 方面现在有什么新技术？"
    logger.info(retriever.get(query, "compact"))


def custom():
    def search(query: str, n: int) -> List[str]:
        response = requests.get(
            "https://open-procedures.replit.app/search/",
            params={"query": query},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()["procedures"]

    retriever = Retriever.Custom(search)
    query = "计算圆周率"
    logger.info(retriever.search(query, 3))


if __name__ == "__main__":
    BM25()
    bing()
    combine()
    custom()
