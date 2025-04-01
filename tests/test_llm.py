from __future__ import annotations

from typing import Any
from unittest.mock import ANY, MagicMock

import pytest
from pydantic import BaseModel

from uglychain.client import Client
from uglychain.config import config
from uglychain.llm import _gen_content, _gen_messages, _get_map_keys, gen_prompt, llm, process_stream_resopnse


class SampleModel(BaseModel):
    content: str


def create_mock_choice(content: str) -> type[Any]:
    return type("Choice", (object,), {"message": type("Message", (object,), {"content": content})})


def mock_generate(model, messages, **kwargs):
    n = 1
    if "n" in kwargs and kwargs["n"]:
        n = kwargs["n"]
    return [create_mock_choice("Test response")] * n


@pytest.fixture
def setup_client(mocker):
    mocker.patch("uglychain.client.Client.generate", mock_generate)


def test_process_stream_response_normal_content():
    mock_response = [
        MagicMock(delta=MagicMock(content="Hello", reasoning_content=None)),
        MagicMock(delta=MagicMock(content=" World", reasoning_content=None)),
    ]
    result = list(process_stream_resopnse(mock_response))
    assert result == ["Hello", " World"]


def test_process_stream_response_with_thinking():
    mock_response = [
        MagicMock(delta=MagicMock(content=None, reasoning_content="Thinking")),
        MagicMock(delta=MagicMock(content=None, reasoning_content=" deeply")),
    ]
    result = list(process_stream_resopnse(mock_response))
    assert result == ["<thinking>\n", "Thinking", " deeply", "\n</thinking>\n"]


def test_process_stream_response_mixed_content():
    mock_response = [
        MagicMock(delta=MagicMock(content="Hello", reasoning_content=None)),
        MagicMock(delta=MagicMock(content=None, reasoning_content="Thinking")),
        MagicMock(delta=MagicMock(content=" World", reasoning_content=None)),
    ]
    result = list(process_stream_resopnse(mock_response))
    assert result == ["Hello", "<thinking>\n", "Thinking", "\n</thinking>\n", " World"]


def test_process_stream_response_closes_unclosed_thinking():
    mock_response = [
        MagicMock(delta=MagicMock(content=None, reasoning_content="Thinking")),
    ]
    result = list(process_stream_resopnse(mock_response))
    assert result == ["<thinking>\n", "Thinking", "\n</thinking>\n"]


def test_llm_decorator(setup_client):
    @llm("test:model", n=None)
    def sample_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_zero_result(mocker):
    @llm
    def sample_prompt() -> str:
        return "Hello, world!"

    mocker.patch("uglychain.client.Client.generate", lambda *args, **kwargs: [])

    with pytest.raises(ValueError, match="模型未返回任何选择"):
        sample_prompt()


def test_llm_decorator_with_basemodel(mocker):
    @llm(model="test:model")  # type: ignore
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    mocker.patch(
        "uglychain.client.Client.generate", lambda *args, **kwargs: [create_mock_choice('{"content": "Test response"}')]
    )

    result = sample_prompt()
    assert result == SampleModel(content="Test response")


@pytest.mark.parametrize("n", [1, 2])
def test_llm_decorator_with_list_str(setup_client, n):
    @llm(model="test:model", n=n)
    def sample_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt()
    assert result == ["Test response"] * n


@pytest.mark.parametrize("n", [1, 2])
def test_llm_decorator_with_list_basemodel(mocker, n):
    @llm(model="test:model", n=n)  # type: ignore
    def sample_prompt() -> SampleModel:
        return "Hello, world!"  # type: ignore

    mocker.patch(
        "uglychain.client.Client.generate",
        lambda *args, **kwargs: [create_mock_choice('{"content": "Test response"}')] * n,
    )

    result = sample_prompt()
    assert result == [SampleModel(content="Test response")] * n


def test_llm_decorator_with_response_format(mocker):
    @llm(model="test:model", response_format=SampleModel)
    def sample_prompt() -> str:
        return "Hello, world!"  # type: ignore

    mocker.patch(
        "uglychain.client.Client.generate", lambda *args, **kwargs: [create_mock_choice('{"content": "Test response"}')]
    )

    result = sample_prompt()
    assert result == SampleModel(content="Test response")


def test_llm_decorator_without_return_annotation(setup_client):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    result = sample_prompt()
    assert result == "Test response"


def test_llm_decorator_with_need_retry(setup_client):
    @llm(model="test:model", need_retry=True)
    def sample_prompt() -> str:
        return "Hello, world!"

    result = sample_prompt()
    assert result == "Test response"


@pytest.mark.parametrize("return_value", [123, 456])
def test_llm_decorator_with_invalid_return_type(setup_client, return_value):
    @llm(model="test:model")  # type: ignore
    def sample_prompt() -> int:
        return return_value  # type: ignore

    with pytest.raises(TypeError):
        sample_prompt()


@pytest.mark.parametrize("api_params", [{}, {"param1": "value1"}])
def test_llm_decorator_with_empty_api_params(setup_client, api_params):
    @llm(model="test:model")
    def sample_prompt():
        return "Hello, world!"

    result = sample_prompt(api_params=api_params)  # type: ignore
    assert result == "Test response"


@pytest.mark.parametrize("arg1, arg2", [(["a", "b"], ["c"]), (["x"], ["y", "z"])])
def test_llm_decorator_with_inconsistent_list_lengths(arg1, arg2):
    @llm(model="test:model", map_keys=["arg1", "arg2"])
    def sample_prompt(arg1: list[str], arg2: list[str]) -> str:
        return "Hello, world!"

    with pytest.raises(ValueError, match="prompt_args 和 prompt_kwargs 中的 map_key 列表必须具有相同的长度"):
        sample_prompt(arg1, arg2)


@pytest.mark.parametrize("arg1", [["a", "b"], ["x", "y", "z"]])
def test_llm_decorator_with_n_and_list_length_conflict(arg1):
    @llm(model="test:model", map_keys=["arg1"], n=2)
    def sample_prompt(arg1: list[str]) -> str:
        return "Hello, world!"

    with pytest.raises(ValueError, match="n > 1 和列表长度 > 1 不能同时成立"):
        sample_prompt(arg1)


@pytest.mark.parametrize("arg1,n", [(["a"], 2), (["x", "y", "z"], 1)])
def test_llm_decorator_with_n_or_list_length_with_stream_conflict(arg1, n):
    @llm(model="test:model", map_keys=["arg1"], n=n, stream=True)
    def sample_prompt(arg1: list[str]) -> str:
        return "Hello, world!"

    with pytest.raises(ValueError, match="stream 不能与列表长度 > 1 同时成立"):
        sample_prompt(arg1)


@pytest.mark.parametrize("arg1", [["a", "b", "c"], ["x", "y", "z"]])
def test_llm_decorator_with_parallel_processing(mocker, arg1):
    @llm(model="test:model", map_keys=["arg1"])
    def sample_prompt(arg1: list[str]) -> str:
        "System prompt"
        return arg1  # type: ignore

    mocker.patch(
        "uglychain.client.Client.generate",
        lambda model, messages, **kwargs: [create_mock_choice(messages[1]["content"][0]["text"])],
    )

    config.use_parallel_processing = True
    results = sample_prompt(arg1)
    assert set(results) == set(arg1)


def test_llm_decorator_with_tools(mocker):
    def mock_tool():
        pass

    @llm(model="test:model", tools=[mock_tool])
    def sample_prompt() -> str:
        return "Hello, world!"

    mock_generate = mocker.patch.object(Client, "generate", return_value=[create_mock_choice("Test response")])
    sample_prompt()
    mock_generate.assert_called_once_with(
        "test:model", [{"role": "user", "content": _gen_content("Hello, world!")}], tools=ANY
    )
    # assert result == "Test response"


def test_llm_decorator_with_invalid_tools_params(mocker):
    config.default_api_params = {"tools": "test"}

    @llm(model="test:model")
    def sample_prompt() -> str:
        return "Hello, world!"

    mock_generate = mocker.patch.object(Client, "generate", return_value=[create_mock_choice("Test response")])
    sample_prompt(api_params={"tools": "test"})  # type: ignore
    mock_generate.assert_called_once_with("test:model", [{"role": "user", "content": _gen_content("Hello, world!")}])
    # assert result == "Test response"


def test_gen_messages_with_string():
    def sample_prompt():
        """System message"""
        return "User message"

    result = _gen_messages("User message", sample_prompt)
    expected = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": _gen_content("User message")},
    ]
    assert result == expected


def test_gen_messages_without_docstring():
    def sample_prompt():  # type: ignore
        return "User message"

    result = _gen_messages("User message", sample_prompt)
    expected = [
        {"role": "user", "content": _gen_content("User message")},
    ]
    assert result == expected

    def sample_prompt():
        return [{"role": "user", "content": "User message"}]

    result = _gen_messages([{"role": "user", "content": "User message"}], sample_prompt)
    expected = [{"role": "user", "content": "User message"}]
    assert result == expected


def test_gen_messages_with_messages_type():
    def sample_prompt():
        """System message"""
        return [{"role": "user", "content": "User message"}]

    result = _gen_messages([{"role": "user", "content": "User message"}], sample_prompt)
    expected = [{"role": "system", "content": "System message"}, {"role": "user", "content": "User message"}]
    assert result == expected


@pytest.mark.parametrize("input", [12345, [], None, "", (1), {"a": 2}])
def test_gen_messages_with_invalid_type(input):
    def sample_prompt():
        return input

    with pytest.raises(TypeError, match="Expected prompt_ret to be a str or list of Messages and not empty"):
        _gen_messages(input, sample_prompt)  # type: ignore


@pytest.mark.parametrize("map_keys", [None, []])
def test_get_map_keys_with_empty_map_keys(map_keys):
    def sample_prompt(arg1: str, arg2: str):
        return "Hello, world!"

    result = _get_map_keys(sample_prompt, ("a", "b"), {}, map_keys=map_keys)
    assert result == (1, set(), set())


def test_get_map_keys_with_different_list_lengths():
    def sample_prompt(arg1: list[str], arg2: list[str]):
        return "Hello, world!"

    with pytest.raises(ValueError, match="prompt_args 和 prompt_kwargs 中的 map_key 列表必须具有相同的长度"):
        _get_map_keys(sample_prompt, (["a", "b"], ["c"]), {}, ["arg1", "arg2"])


def test_get_map_keys_with_invalid_map_key_type():
    def sample_prompt(arg1: str):
        return "Hello, world!"

    with pytest.raises(ValueError, match="map_key 必须是列表"):
        _get_map_keys(sample_prompt, ("a",), {}, ["arg1"])


def test_gen_prompt_with_empty_value():
    def sample_prompt(arg1, arg2):
        return None

    result = gen_prompt(sample_prompt, arg1="value1", arg2=None)
    expected = "<arg1>\nvalue1\n</arg1>"
    assert result == expected


@pytest.mark.parametrize(
    "args, expected",
    [
        (("value1", "value2"), "<arg1>\nvalue1\n</arg1>\n<arg2>\nvalue2\n</arg2>"),
        ((123, ["a", "b"]), "<arg1>\n123\n</arg1>\n<arg2>\n['a', 'b']\n</arg2>"),
    ],
)
def test_gen_prompt(args, expected):
    def sample_prompt(arg1, arg2):
        return None

    result = gen_prompt(sample_prompt, *args)
    assert result == expected


@pytest.mark.parametrize(
    "model,image_input, expected_url",
    [
        (
            "openai:gpt-4o",
            "https://example.com/image.jpg",
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
        ),
        (
            "openai:gpt-4o-mini",
            "base64encodedstring",
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,base64encodedstring"}},
        ),
        ("test:model", "https://example.com/image.jpg", None),
    ],
)
def test_llm_decorator_with_image(mocker, model, image_input, expected_url):
    @llm(model=model)
    def sample_prompt() -> str:
        return "Hello, world!"

    mock_generate = mocker.patch.object(Client, "generate", return_value=[create_mock_choice("Test response")])

    result = sample_prompt(image=image_input)  # type: ignore
    content = _gen_content("Hello, world!")
    if expected_url:
        content.append(expected_url)
    expected_message = [
        {
            "role": "user",
            "content": content,
        },
    ]
    mock_generate.assert_called_with(model, expected_message)
    assert result == "Test response"


@pytest.mark.parametrize(
    "image,expected",
    [
        (
            "https://example.com/image.jpg",
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "User message"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
                    ],
                }
            ],
        ),
        (
            "base64encodedstring",
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "User message"},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,base64encodedstring"}},
                    ],
                }
            ],
        ),
        (None, [{"role": "user", "content": [{"type": "text", "text": "User message"}]}]),
        (
            ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "User message"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/img1.jpg"}},
                        {"type": "image_url", "image_url": {"url": "https://example.com/img2.jpg"}},
                    ],
                }
            ],
        ),
    ],
)
def test_gen_messages_with_image(image, expected):
    def sample_prompt():
        return "User message"

    # Test with single image URL
    result = _gen_messages("User message", sample_prompt, image)
    assert result == expected
