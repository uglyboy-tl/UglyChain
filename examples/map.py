from loguru import logger

from examples.schema import AUTHOR, UserDetail
from uglychain import MapChain, Model


def map(model: Model | None = None):
    if model:
        llm = MapChain(model=model)
    else:
        llm = MapChain()
    input = [
        "How old are you?",
        "What is the meaning of life?",
        "What is the hottest day of the year?",
    ]
    for item in llm(input):
        logger.info(item)


def map_input(model: Model | None = None):
    if model:
        llm = MapChain(
            prompt_template="{book}的{position}是谁？",
            model=model,
            response_model=AUTHOR,
            map_keys=["book"],
        )
    else:
        llm = MapChain(
            prompt_template="{book}的{position}是谁？",
            response_model=AUTHOR,
            map_keys=["book"],
        )
    input = [
        "《红楼梦》",
        "《西游记》",
        "《三国演义》",
        "《水浒传》",
    ]
    for item in llm(book=input, position="作者"):
        logger.info(item)


def instructor(model: Model | None = None):
    if model:
        llm = MapChain(model=model, response_model=UserDetail)
    else:
        llm = MapChain(response_model=UserDetail)
    input = ["Extract Jason is a boy", "Extract Jason is a girl", "Extract Robin is a boy", "Extract Misty is a girl"]
    for item in llm(input):
        logger.info(item)


if __name__ == "__main__":
    # map()
    # map_input(Model.YI_200K)
    instructor()
