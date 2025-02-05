from __future__ import annotations

from uglychain import llm


class Index:
    pass


class RAG:
    @staticmethod
    def get_embedding(text: str) -> list[float]:
        """Get the embedding of a text."""
        return []

    @staticmethod
    def create_index(embeddings: list[list[float]]) -> Index:
        """Create an index from a list of embeddings."""
        return Index()

    @staticmethod
    def search_index(
        index: Index, query_embedding: list[float], top_k: int
    ) -> tuple[list[tuple[int, float]], list[float]]:
        """Search the index for the top k results."""
        return [], []


texts: list[str] = []
question = "What is the capital of France?"

embeddings = [RAG.get_embedding(text) for text in texts]
index = RAG.create_index(embeddings)
query_embedding = RAG.get_embedding(question)
indices, _ = RAG.search_index(index, query_embedding, top_k=1)
relevant_text = texts[indices[0][0]]


@llm
def rag(question: str, context: str):
    return f"Question: {question}\nContext: {context}\nAnswer: "


rag(question=question, context=relevant_text)
