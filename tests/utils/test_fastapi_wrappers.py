from __future__ import annotations

import inspect
from typing import Any

import pytest
from pydantic import BaseModel

from uglychain.utils.fastapi_wrappers import append_to_signature, json_post_endpoint


@pytest.mark.asyncio
async def test_json_post_endpoint_with_valid_function():
    """Test that json_post_endpoint correctly wraps a valid function."""

    def sample_function(name: str, age: int, is_active: bool = True) -> dict[str, Any]:
        return {"name": name, "age": age, "is_active": is_active}

    wrapped = json_post_endpoint(sample_function)

    # Check that the wrapper has the correct signature
    sig = inspect.signature(wrapped)
    assert len(sig.parameters) == 1
    param = list(sig.parameters.values())[0]
    assert param.name == "request"
    assert issubclass(param.annotation, BaseModel)

    # Check that the request model has the correct fields
    request_model = param.annotation
    assert "name" in request_model.__annotations__
    # In Pydantic v2, annotations might be stored as strings
    assert request_model.__annotations__["name"] in (str, "str")
    assert "age" in request_model.__annotations__
    assert request_model.__annotations__["age"] in (int, "int")
    assert "is_active" in request_model.__annotations__
    assert request_model.__annotations__["is_active"] in (bool, "bool")

    # Create a request model instance and call the wrapper
    request_instance = request_model(name="Test", age=30)
    result = await wrapped(request_instance)
    assert result == {"name": "Test", "age": 30, "is_active": True}


def test_json_post_endpoint_with_var_args():
    """Test that json_post_endpoint raises TypeError for functions with *args."""

    def invalid_function(name: str, *args: str) -> dict[str, Any]:
        return {"name": name, "args": args}

    with pytest.raises(TypeError) as excinfo:
        json_post_endpoint(invalid_function)

    # The error message contains zero-width spaces, so we check for the function name instead
    assert "Function invalid_function cannot have" in str(excinfo.value)


def test_json_post_endpoint_with_var_kwargs():
    """Test that json_post_endpoint raises TypeError for functions with **kwargs."""

    def invalid_function(name: str, **kwargs: Any) -> dict[str, Any]:
        return {"name": name, **kwargs}

    with pytest.raises(TypeError) as excinfo:
        json_post_endpoint(invalid_function)

    # The error message contains zero-width spaces, so we check for the function name instead
    assert "Function invalid_function cannot have" in str(excinfo.value)


def test_json_post_endpoint_without_type_annotation():
    """Test that json_post_endpoint raises TypeError for parameters without type annotations."""

    def invalid_function(name, age: int) -> dict[str, Any]:
        return {"name": name, "age": age}

    with pytest.raises(TypeError) as excinfo:
        json_post_endpoint(invalid_function)

    assert "must be type annotated" in str(excinfo.value)


def test_append_to_signature():
    """Test that append_to_signature correctly modifies a function's signature."""

    def original_function():
        pass

    param1 = inspect.Parameter("param1", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
    param2 = inspect.Parameter("param2", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int, default=0)

    modified = append_to_signature(original_function, param1, param2)

    # Check that the function was modified correctly
    assert modified is original_function  # Should return the same function object

    # Check that the signature was updated
    sig = inspect.signature(modified)
    assert len(sig.parameters) == 2
    assert "param1" in sig.parameters
    assert sig.parameters["param1"].annotation is str
    assert "param2" in sig.parameters
    assert sig.parameters["param2"].annotation is int
    assert sig.parameters["param2"].default == 0


@pytest.mark.asyncio
async def test_wrapper_function():
    """Test the wrapper function created by json_post_endpoint."""

    def sample_function(name: str, age: int, is_active: bool = True) -> dict[str, Any]:
        return {"name": name, "age": age, "is_active": is_active}

    wrapped = json_post_endpoint(sample_function)

    # Get the request model
    request_model = list(inspect.signature(wrapped).parameters.values())[0].annotation

    # Create a request instance and call the wrapper
    request = request_model(name="Test", age=25, is_active=False)
    result = await wrapped(request)

    assert result == {"name": "Test", "age": 25, "is_active": False}
