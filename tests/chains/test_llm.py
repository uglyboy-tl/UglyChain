from examples.schema import Gender, UserDetail
from uglychain import LLM


def test_llm():
    llm = LLM()
    assert isinstance(llm("你是谁？"), str)


def test_instructor():
    llm = LLM(response_model=UserDetail)
    obj = llm("Extract Jason is a boy")
    assert isinstance(obj, UserDetail)
    assert obj.name == "Jason"
    assert obj.gender == Gender.MALE
