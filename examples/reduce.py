from typing import Any, Optional

from loguru import logger

from uglychain import Model, ReduceChain


def reduce(model: Optional[Model] = None):
    if model:
        llm = ReduceChain(model=model)
    else:
        llm = ReduceChain()
    input = [
        "请写出这句诗的下一句",
        "请写出这句诗的下一句",
        "请写出这句诗的下一句",
    ]
    logger.info(llm(input=input, history="锄禾日当午"))


def reduce_function(model: Optional[Model] = None):
    def string(obj: Any) -> str:
        """Converts an object to a string.

        Args:
            obj (Any): The object to be converted.
        """
        return str(obj)

    tools = [string]
    if model:
        llm = ReduceChain(model=model, tools=tools)
    else:
        llm = ReduceChain(tools=tools)
    input = [
        "请写出这句诗的下一句",
        "请写出这句诗的下一句",
        "请写出这句诗的下一句",
    ]
    logger.info(llm(input=input, history="锄禾日当午"))


if __name__ == "__main__":
    #reduce()
    reduce_function(Model.GPT4_TURBO)
