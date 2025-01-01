from __future__ import annotations

from collections.abc import Callable

from examples.schema import get_current_weather, search_baidu

from uglychain import config
from uglychain.react import react


@react("openai:gpt-4o", [get_current_weather, search_baidu])
def test():
    return "What's the weather in San Francisco?"


if __name__ == "__main__":
    config.verbose = True
    test()
