from uglychain import LLM


def text_completion(prompt: str) -> str:
    """A tool that uses LLM to generate, summarize, and/or analyze text and code.

    Args:
        prompt (str): The prompt to use for text generation.
    """
    llm = LLM()
    return llm(prompt)
