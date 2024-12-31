from __future__ import annotations

from enum import Enum

from uglychain import config, llm


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


def functian_call():
    @llm("openai:gpt-4o-mini", tools=[get_current_weather])
    def _tools():
        return "What's the weather in Beijing?"

    print(_tools())


def tools():
    @llm("openai:gpt-4o-mini", tools=[get_current_weather, search_baidu, search_google, search_bing])
    def _tools():
        return "牛顿生于哪一年？请搜索查询"

    print(_tools())


if __name__ == "__main__":
    # functian_call()
    tools()
