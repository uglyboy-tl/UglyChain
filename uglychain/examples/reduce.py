from loguru import logger

from uglychain import ReduceChain, Model


def reduce(model: Model | None = None):
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


if __name__ == "__main__":
    reduce(Model.YI)
