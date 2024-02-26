from loguru import logger

from examples.schema import UserDetail
from uglychain import LLM, Model
from uglychain.llm.provider.yi import Yi


class CustomModel(Model):
    YI_NEW = (Yi, {"model": "yi-34b-chat-0205", "MAX_TOKENS": 4096})


def llm():
    llm = LLM(model=CustomModel.YI_NEW)
    logger.info(llm("你是谁？"))

def prompt():
    llm = LLM("{cite} 的市长是谁？", CustomModel.YI_NEW)
    logger.info(llm("上海"))


def instructor():
    llm = LLM(model=CustomModel.YI, response_model=UserDetail)
    logger.info(llm("Extract Jason is a boy"))


if __name__ == "__main__":
    #llm()
    #prompt()
    instructor()

