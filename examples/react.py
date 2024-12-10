from __future__ import annotations

import sys
from collections.abc import Callable
from enum import Enum

from loguru import logger

from uglychain import Model
from uglychain.chains.react_bad import ReActChain

# from uglychain.chains.react import ReActChain

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
    return "晴天，25华氏度"


def search_baidu(query: str) -> str:
    """Search Baidu for the query.

    Args:
        query (str): The query to search.
    """
    return "牛顿出生于1642年"


def react(model: Model | None = None):
    tools: list[Callable] = [get_current_weather, search_baidu]
    if model:
        llm = ReActChain(model=model, tools=tools)
    else:
        llm = ReActChain(tools=tools)

    # response = llm("牛顿生于哪一年")
    response = llm("What's the weather in San Francisco?")
    logger.info(response)


if __name__ == "__main__":
    react()
