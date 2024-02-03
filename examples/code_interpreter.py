import sys

from loguru import logger

from uglychain import Model
from uglychain.woker.code_interpreter import CodeInterpreter

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")

worker = CodeInterpreter(model=Model.YI_32K)
input = "我买房贷款了187万，贷款的利率是4.9%，贷款期限是30年，每月还款多少？"
logger.info(worker.run(input))
