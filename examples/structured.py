from __future__ import annotations

from examples.schema import UserDetail

from uglychain import config, llm


@llm(response_format=UserDetail)
def test(prompt: str):
    return prompt


if __name__ == "__main__":
    config.verbose = True
    test("Extract Jason is a boy")
