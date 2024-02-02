# import sys

from loguru import logger

from uglychain import Model
from uglychain.woker.summary import Summary

# logger.remove()
# logger.add(sink=sys.stdout, level="TRACE")

worker = Summary("你是一个总结专家。", model=Model.YI_32K)
with open("examples/summary.md") as f:
    input = f.read()
    logger.info(worker.run(input))
