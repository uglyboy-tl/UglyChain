import sys

from loguru import logger

from uglychain import Model, finish, run_function
from uglychain.llm import FunctionCall
from uglychain.woker.code_interpreter import CodeInterpreter, run_code

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")

worker = CodeInterpreter(model=Model.YI_32K)
input = "我买房贷款了187万，贷款的年利率是4.9%，贷款期限是30年，每月还款多少？"
# input = """"""
response = worker.run(input)
logger.info(worker.run(input))
assert isinstance(response, FunctionCall)
logger.info(run_function([run_code, finish], response))
