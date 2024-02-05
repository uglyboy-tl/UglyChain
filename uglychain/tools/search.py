from uglychain.retrievers import get_retriever


def search_knowledgebase(query: str) -> str:
    """Searches the knowledge base for an answer to the technical question

    Args:
        query (str): The search query to use to search the knowledge base

    Returns:
        str: The answer to the query
    """
    retriever = get_retriever()
    return retriever.get(query)
