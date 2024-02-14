from uglychain.retrievers import Retriever


def search_knowledgebase(query: str) -> str:
    """Searches the knowledge base for an answer to the technical question

    Args:
        query (str): The search query to use to search the knowledge base

    Returns:
        str: The answer to the query
    """
    retriever = Retriever.Bing()
    return retriever.get(query, "compact", 5)
