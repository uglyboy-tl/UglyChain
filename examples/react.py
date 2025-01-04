from __future__ import annotations

from collections.abc import Callable

from examples.schema import get_current_weather, search_baidu

from uglychain import config
from uglychain.react import react


@react("openai:gpt-4o-mini", [get_current_weather, search_baidu])
def test():
    # return "What's the weather in San Francisco?"
    return "牛顿生于哪一年？"


if __name__ == "__main__":
    config.verbose = True
    print(test())
