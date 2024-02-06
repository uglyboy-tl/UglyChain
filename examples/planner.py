import sys

from loguru import logger

from uglychain import Model
from uglychain.tools import run_code, search_knowledgebase, text_completion
from uglychain.woker.planner import Planner, Tasks

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")


def planner(model: Model | None = None):
    objective = "安装零一万物的 YI-32K 模型"
    # objective = "让世界更加和平"
    tools = [search_knowledgebase, run_code]
    if model:
        worker = Planner(model=model, tools=tools)
    else:
        worker = Planner(tools=tools)
    tasks = worker.run(objective)
    # for task in tasks.tasks:
    #    logger.info(task)
    logger.info(tasks.pretty)
    return tasks


def run_single_task(tasks: Tasks):
    def execute(params: str, dependent_task_outputs: str, objective: str) -> str:
        prompt = f"Complete your assigned task based on the objective and only based on information provided in the dependent task output, if provided. \n###\nYour objective: {objective}. \n###\nYour task: {params} \n###\nDependent tasks output: {dependent_task_outputs}  \n###\nYour task: {params}\n###\nRESPONSE"
        return text_completion(prompt)

    task = tasks.tasks[0]
    task_output = tasks.execute_task(task, execute, "安装零一万物的 YI-32K 模型")
    tools = [search_knowledgebase, run_code]
    worker = Planner(tools=tools)
    tasks = worker.run(tasks=tasks, task_output=task_output)
    logger.info(tasks.pretty)


if __name__ == "__main__":
    tasks = planner(Model.YI)
    run_single_task(tasks)
