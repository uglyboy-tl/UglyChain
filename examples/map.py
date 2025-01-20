from __future__ import annotations

from examples.schema import AUTHOR, UserDetail

from uglychain import config, llm


def map():
    @llm(map_keys=["input"])
    def _map(input: list[str]):
        return f"{input}"

    input = [
        "How old are you?",
        "What is the meaning of life?",
        "What is the hottest day of the year?",
    ]
    for item in _map(input):
        print(item)


def map_input():
    @llm(map_keys=["book"], response_format=AUTHOR)
    def _map(book: list[str], position: str):
        return f"{book}的{position}是谁？"

    input = [
        "《红楼梦》",
        "《西游记》",
        "《三国演义》",
        "《水浒传》",
    ]
    for item in _map(book=input, position="作者"):
        print(item)


def test():
    @llm("openai:gpt-4o-mini", map_keys=["input"], response_format=UserDetail)
    def _map(input: list[str]):
        return f"{input}"

    input = ["Extract Jason is a boy", "Extract Jason is a girl", "Extract Robin is a boy", "Extract Misty is a girl"]
    for item in _map(input):
        print(item)


if __name__ == "__main__":
    config.verbose = True
    config.use_parallel_processing = True
    # map()
    map_input()
    # test()
