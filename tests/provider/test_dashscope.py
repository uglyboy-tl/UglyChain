import pytest
from uglychain import LLM, Model
from examples.instructor import UserDetail, Gender

@pytest.mark.parametrize("model", [Model.QWEN, Model.QWEN_28K, Model.QWEN_TURBO, Model.QWEN_PLUS])
def test_llm(model):
    llm = LLM(model=model)
    assert isinstance(llm("你是谁？"), str)

@pytest.mark.parametrize("model", [Model.QWEN, Model.QWEN_28K, Model.QWEN_TURBO, Model.QWEN_PLUS])
def test_instructor(model):
    llm = LLM(model=model, response_model=UserDetail)
    obj = llm("Extract Jason is a boy")
    assert isinstance(obj, UserDetail)
    assert obj.name == "Jason"
    assert obj.gender == Gender.MALE