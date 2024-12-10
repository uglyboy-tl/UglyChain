from __future__ import annotations

from examples.schema import AUTHOR

from uglychain import MapChain


def test_map():
    llm = MapChain()
    input = [
        "How old are you?",
        "What is the meaning of life?",
        "What is the hottest day of the year?",
    ]
    output = llm(input)
    assert isinstance(output, list)
    assert len(output) == 3
    assert isinstance(output[0], str)


def test_instructor():
    llm = MapChain(
        prompt_template="{book}的{position}是谁？",
        response_model=AUTHOR,
        map_keys=["book"],
    )
    input = [
        "《红楼梦》",
        "《西游记》",
        "《三国演义》",
        "《水浒传》",
    ]
    output = llm(book=input, position="作者")
    assert isinstance(output, list)
    assert len(output) == 4
    assert isinstance(output[0], AUTHOR)
