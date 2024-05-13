from enum import Enum
from typing import Callable, List

import pytest

from uglychain import Model
from uglychain.chains.react_bad import ReActChain


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


@pytest.mark.parametrize(
    "model", [Model.GPT3_TURBO, Model.YI, Model.YI_TURBO, Model.QWEN, Model.GLM3, Model.BAICHUAN_TURBO]
)
def test_react1(model):
    tools: List[Callable] = [get_current_weather, search_baidu]
    llm = ReActChain(model=model, tools=tools)

    response = llm("What's the weather in San Francisco?")
    assert response.find("25") >= 0


@pytest.mark.parametrize(
    "model", [Model.GPT3_TURBO, Model.YI, Model.YI_TURBO, Model.QWEN, Model.GLM4, Model.BAICHUAN_TURBO]
)
def test_react2(model):
    tools: List[Callable] = [get_current_weather, search_baidu]
    llm = ReActChain(model=model, tools=tools)

    response = llm("牛顿生于哪一年")
    assert response.find("1642") >= 0 or response.find("1643") >= 0
