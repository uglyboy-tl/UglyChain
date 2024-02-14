from typing import List

from uglychain.chains import LLM, MapChain, ReduceChain

REDUCE_PROMPT = """The original query is as follows: {query_str}
We have provided an existing answer: {history}
We have the opportunity to refine the existing answer (only if needed) with some more context below.
------------
{context_str}
------------
Given the new context, refine the original answer to better answer the query. If the context isn't useful, return the original answer.
Refined Answer:
"""

DEFAULT_PROMPT = """Context information is below.
---------------------
{context_str}
---------------------
Given the context information and not prior knowledge, answer the query.
Query: {query_str}
Answer:
"""

SUMMARY_PROMPT = """
Write a summary of the following. Try to use only the information provided. Try to include as many key details as possible.


{context_str}


SUMMARY:
"""

ROLE = """You are to answer the query based on the context. You need to answer with the same language as the question use."""


def answer_with_llm(
    query: str,
    context: List[str],
):
    llm = LLM(DEFAULT_PROMPT, system_prompt=ROLE)
    return llm(query_str=query, context_str=context)


def answer_with_reduce_llm(
    query: str,
    context: List[str],
):
    llm = ReduceChain(REDUCE_PROMPT, reduce_keys=["context_str"], system_prompt=ROLE)
    return llm(query_str=query, context_str=context)


def answer_with_map_llm(
    query: str,
    context: List[str],
):
    llm = MapChain(SUMMARY_PROMPT, map_keys=["context_str"])
    summaries = llm(context_str=context)
    return answer_with_llm(query, summaries)
