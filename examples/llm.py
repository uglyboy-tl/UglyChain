from __future__ import annotations

import sys

from examples.schema import UserDetail
from loguru import logger

from uglychain import LLM, Model

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")


def llm(model: Model | None = None):
    if model:
        llm = LLM(model=model)
    else:
        llm = LLM()
    logger.info(llm("你是谁？"))


def prompt(model: Model | None = None):
    if model:
        llm = LLM("{cite} 的市长是谁？", model)
    else:
        llm = LLM("{cite} 的市长是谁？")
    logger.info(llm("上海"))


def instructor(model: Model | None = None):
    if model:
        llm = LLM(model=model, response_model=UserDetail)
    else:
        llm = LLM(response_model=UserDetail)
    logger.info(llm("Extract Jason is a boy"))


if __name__ == "__main__":
    llm(Model.YI)
    llm(Model.GLM3)
    llm(Model.QWEN)
    llm(Model.GPT3_TURBO)
    llm(Model.COPILOT3_TURBO)
    llm(Model.BAICHUAN_TURBO)
    prompt(Model.YI)
    instructor(Model.YI)
