from __future__ import annotations

import pytest
from examples.schema import Gender, UserDetail

from uglychain import LLM, Model


@pytest.mark.parametrize("model", [Model.SPARK])
def test_llm(model):
    llm = LLM(model=model)
    assert isinstance(llm("你是谁？"), str)


@pytest.mark.parametrize("model", [Model.SPARK])
def test_instructor(model):
    llm = LLM(model=model, response_model=UserDetail)
    obj = llm("Extract Jason is a boy")
    assert isinstance(obj, UserDetail)
    assert obj.name == "Jason"
    assert obj.gender == Gender.MALE
