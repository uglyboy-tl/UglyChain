import pytest

from examples.instructor import Gender, UserDetail
from uglychain import LLM, Model


@pytest.mark.parametrize(
    "model", [Model.GPT3_TURBO, Model.GPT3_TURBO_16K, Model.GPT4, Model.GPT4_TURBO]
)
def test_llm(model):
    llm = LLM(model=model)
    assert isinstance(llm("你是谁？"), str)


@pytest.mark.parametrize(
    "model", [Model.GPT3_TURBO, Model.GPT3_TURBO_16K, Model.GPT4, Model.GPT4_TURBO]
)
def test_instructor(model):
    llm = LLM(model=model, response_model=UserDetail)
    obj = llm("Extract Jason is a boy")
    assert isinstance(obj, UserDetail)
    assert obj.name == "Jason"
    assert obj.gender == Gender.MALE
