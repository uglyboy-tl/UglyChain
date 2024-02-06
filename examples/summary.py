# import sys

from loguru import logger

from uglychain import Model
from uglychain.worker.summary import Summary

# logger.remove()
# logger.add(sink=sys.stdout, level="TRACE")

worker = Summary(model=Model.YI_32K, use_reduce=True, char_limit=1000)
with open("examples/summary.md") as f:
    input = f.read()
    logger.info(worker.run(input))
