import sys
from enum import Enum

from loguru import logger

from uglychain import LLM, Model, finish, run_function

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")


class Unit(Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"


def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT) -> str:
    """Get the current weather in a given location.

    Args:
        location (str): The city and state, e.g., San Francisco, CA
        unit (Unit): The unit to use, e.g., fahrenheit or celsius
    """
    return "Weather"


def search_baidu(query: str) -> str:
    """Search Baidu for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}出生于1642年"


def search_google(query: str) -> str:
    """Search Google for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个后端工程师"


def search_bing(query: str) -> str:
    """Search Bing for the query.

    Args:
        query (str): The query to search.
    """
    return f"{query}是一个技术博主"


def functian_call(model: Model | None = None):
    tools = [get_current_weather]
    if model:
        llm = LLM(model=model, tools=tools)
    else:
        llm = LLM(tools=tools)
    logger.info(llm("What's the weather in Beijing?"))


def tools(model: Model | None = None):
    tools = [get_current_weather, search_baidu, search_google, search_bing, finish]
    if model:
        llm = LLM(
            model=model,
            tools=tools,
        )
    else:
        llm = LLM(tools=tools)
    response = llm("牛顿生于哪一年？")
    logger.debug(response)
    logger.info(run_function(tools, response))


if __name__ == "__main__":
    functian_call()
    tools()
