import sys

from loguru import logger

from uglychain import Model
from uglychain.woker.ci import CodeInterpreter

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")

worker = CodeInterpreter(model=Model.YI_32K)
input = "What operating system are we on?"
logger.info(worker.run(input))
