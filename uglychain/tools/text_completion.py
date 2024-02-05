from uglychain import LLM, Model


def text_completion(prompt: str) -> str:
    """Text completion tool.

    Args:
        prompt (str): The prompt to complete.
    """
    llm = LLM(model=Model.YI_32K)
    return llm(prompt)
