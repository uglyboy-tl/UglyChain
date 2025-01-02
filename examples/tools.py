from __future__ import annotations

from enum import Enum
from typing import cast

from examples.schema import get_current_weather, search_baidu, search_bing, search_google

from uglychain import config, llm
from uglychain.tools import ToolResopnse, get_tools_schema


def functian_call():
    @llm(
        "openai:gpt-4o-mini",
        tools=get_tools_schema([get_current_weather]),
        tool_choice={"type": "function", "function": {"name": get_current_weather.__name__}},
    )
    def _tools():
        return "What's the weather in Beijing?"

    response = cast(ToolResopnse, _tools())
    result = get_current_weather(**response.parameters)
    print(result)


def tools():
    @llm("openai:gpt-4o-mini", tools=get_tools_schema([get_current_weather, search_baidu, search_google, search_bing]))
    def _tools():
        return "牛顿生于哪一年？请搜索查询"

    print(_tools())


if __name__ == "__main__":
    functian_call()
    tools()
