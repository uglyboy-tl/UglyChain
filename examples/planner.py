import sys

from loguru import logger

from uglychain import Model
from uglychain.woker.planner import Planner

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")

objective = "安装零一万物的 YI-32K 模型。"
worker = Planner(model=Model.YI_32K)
tasks = worker.run(objective).tasks
for task in tasks:
    logger.info(task)
