from enum import Enum

import pytest

from uglychain import LLM, Model
from uglychain.llm import FunctionCall


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
    return f"{query}是一个技术博主"


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


@pytest.mark.parametrize("model", [Model.GPT3_TURBO, Model.QWEN, Model.YI_32K, Model.YI])
def test_llm_tool(model):
    tools = [get_current_weather]
    llm = LLM(model=model, tools=tools)
    response = llm("What's the weather in Beijing?")
    assert isinstance(response, FunctionCall)
    assert response.name == "get_current_weather"
    assert response.args["location"] == "Beijing"
    assert not hasattr(response.args, "unit") or response.args["unit"] in {"CELSIUS", "FAHRENHEIT"}


@pytest.mark.parametrize("model", [Model.GPT3_TURBO, Model.QWEN, Model.YI_32K, Model.YI])
def test_llm_tools(model):
    tools = [get_current_weather, search_baidu, search_google, search_bing]
    llm = LLM(model=model, tools=tools)
    response = llm("用百度查一查牛顿生于哪一年？")
    assert isinstance(response, FunctionCall)
    assert response.name == "search_baidu"
    assert isinstance(response.args["query"], str)
