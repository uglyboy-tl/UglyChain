#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List

from loguru import logger
from pydantic import BaseModel

from uglychain.chains import LLM
from uglychain.provider import Model

from .base import BaseRetriever
from .model import Retriever

PROMPT = """A question is provided below. Given the question, extract up to {max_keywords} keywords from the text. Focus on extracting the keywords that we can use to best lookup answers to the question. Avoid stopwords. If the keywords is not in English, please translate it to English.
---------------------
{query}
---------------------
"""


class Keywords(BaseModel):
    keywords: List[str]


@dataclass
class CombineRetriever(BaseRetriever):
    retrievers: list[Retriever]
    model: Model = Model.DEFAULT

    def search(self, query: str, n: int = BaseRetriever.default_n) -> List[str]:
        results = []
        if Retriever.Arxiv in self.retrievers or Retriever.Bing in self.retrievers:
            keywords = self.get_kewords(query)
            query_keywords = " ".join(keywords)
            logger.trace(f"query_keywords: {query_keywords}")
        for retriever in self.retrievers:
            instance = retriever()
            if retriever in {Retriever.Arxiv, Retriever.Bing}:
                results.extend(instance.search(query_keywords, n))
            else:
                results.extend(instance.search(query, n))
        return results

    def get_kewords(self, query: str, n: int = 5) -> List[str]:
        llm = LLM(PROMPT, self.model, response_model=Keywords)
        response = llm(query=query, max_keywords=n)
        return response.keywords[:5]
