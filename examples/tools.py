from __future__ import annotations

from enum import Enum

from examples.schema import get_current_weather, search_baidu, search_bing, search_google

from uglychain import config, llm


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
    functian_call()
    # tools()
