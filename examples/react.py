from __future__ import annotations

from examples.schema import get_current_weather, search_baidu
from pydantic import BaseModel

from uglychain import config, react


class Date(BaseModel):
    year: int


@react("openai:gpt-4o-mini", [get_current_weather, search_baidu], response_format=Date)
def test():
    return "牛顿生于哪一年？"


if __name__ == "__main__":
    config.verbose = True
    print(test())
