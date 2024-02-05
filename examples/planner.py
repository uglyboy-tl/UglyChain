import sys

from loguru import logger

from uglychain import Model
from uglychain.tools import run_code, search_knowledgebase
from uglychain.woker.planner import Planner

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")


def planner(model: Model | None = None):
    objective = "安装零一万物的 YI-32K 模型"
    tools = [search_knowledgebase, run_code]
    if model:
        worker = Planner(model=model, tools=tools)
    else:
        worker = Planner(tools=tools)
    tasks = worker.run(objective).tasks
    for task in tasks:
        logger.info(task)


if __name__ == "__main__":
    planner(Model.YI)
