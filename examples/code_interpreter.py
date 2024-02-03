import sys

from loguru import logger

from uglychain import Model, finish, run_function
from uglychain.llm import FunctionCall
from uglychain.woker.code_interpreter import CodeInterpreter, run_code

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")

worker = CodeInterpreter(model=Model.GPT3_TURBO)
input = "我买房贷款了187万，贷款的年利率是4.9%，贷款期限是30年，每月还款多少？"
response = worker.run(input)
logger.info(worker.run(input))
assert isinstance(response, FunctionCall)
# assert isinstance(response.args["language"], Language)
logger.info(run_function([run_code, finish], response))
