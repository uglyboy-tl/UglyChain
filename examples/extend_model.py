from typing import Optional

from loguru import logger

from examples.schema import UserDetail
from uglychain import LLM, MapChain, Model
from uglychain.llm.provider.yi import Yi


class CustomModel(Model):
    YI_NEW = (Yi, {"model": "yi-34b-chat-0205", "MAX_TOKENS": 4096})


def llm():
    llm = LLM(model=CustomModel.DEFAULT)
    logger.info(llm("你是谁？"))


def prompt():
    llm = LLM("{cite} 的市长是谁？", CustomModel.YI_NEW)
    logger.info(llm("上海"))


def instructor():
    llm = LLM(model=CustomModel.YI_NEW, response_model=UserDetail)
    logger.info(llm("Extract Jason is a boy"))


def map_instructor(model: Optional[Model] = None):
    if model:
        llm = MapChain(model=model, response_model=UserDetail)
    else:
        llm = MapChain(response_model=UserDetail)
    llm.show_progress = False
    input = ["Extract Jason is a boy", "Extract Jason is a girl", "Extract Robin is a boy", "Extract Misty is a girl"]
    for item in llm(input):
        logger.info(item)


if __name__ == "__main__":
    #llm()
    #prompt()
    #instructor()
    map_instructor(CustomModel.YI_NEW)
