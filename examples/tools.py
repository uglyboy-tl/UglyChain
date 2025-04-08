from __future__ import annotations

from collections.abc import Callable
from typing import Any

from examples.schema import search_baidu, search_bing, search_google, will_it_rain

from uglychain import config, llm
from uglychain.schema import ToolResponse
from uglychain.tools import function_schema


def get_tools_schema(tools: list[Callable]) -> list[dict[str, Any]]:
    if not tools:
        return []
    return [{"type": "function", "function": function_schema(tool)} for tool in tools]


def functian_call():
    @llm(
        tools=get_tools_schema([will_it_rain]),
        tool_choice={"type": "function", "function": {"name": will_it_rain.__name__}},
    )
    def _tools():
        return "What's the weather in Beijing?"

    response = _tools()
    assert isinstance(response, ToolResponse)
    result = response.run_function([will_it_rain])
    print(result)


def tools():
    @llm(tools=get_tools_schema([will_it_rain, search_baidu, search_google, search_bing]))
    def _tools():
        return "牛顿生于哪一年？请搜索查询"

    print(_tools())


if __name__ == "__main__":
    config.verbose = True
    functian_call()
    tools()
