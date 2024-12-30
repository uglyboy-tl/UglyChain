from __future__ import annotations

from enum import Enum, unique

from pydantic import BaseModel

from uglychain import config, llm
from uglychain.response_format import ResponseModel


@unique
class Gender(Enum):
    FEMALE = "FEMALE"
    MALE = "MALE"


class UserDetail(BaseModel):
    name: str
    gender: Gender


def fc(name: str) -> str:
    return f"{name} is a boy"


@llm("openai:gpt-4o-mini", map_keys=["name"], response_format=UserDetail)
def test(gender: str, name: list[str]):
    return f"{name} is a {gender}"


if __name__ == "__main__":
    config.verbose = True
    config.use_parallel_processing = True
    test("boy", ["Alice", "Bob", "Uglyboy"])
