from __future__ import annotations

import inspect
import textwrap
import warnings
from collections.abc import Callable, Sequence
from typing import Annotated, Any, get_args, get_origin

from openai.lib import _pydantic
from pydantic import BaseModel, ConfigDict, PydanticDeprecationWarning, create_model, validate_arguments
from pydantic.fields import FieldInfo


def function_schema(func: Callable) -> dict[str, Any]:
    pydantic_func = create_schema_from_function(func.__name__, func)
    return convert_pydantic_to_openai_function(pydantic_func)


def convert_pydantic_to_openai_function(
    model: type,
    *,
    rm_titles: bool = True,
) -> dict[str, Any]:
    if hasattr(model, "model_json_schema"):
        parameters = _pydantic.to_strict_json_schema(model)
        if "$defs" in parameters:  # pydantic 2
            parameters.pop("$defs", None)
        title = parameters.pop("title", "")
        default_description = parameters.pop("description", "")
        return {
            "name": model.__name__ or title,
            "description": model.__doc__ or default_description,
            "parameters": _rm_titles(parameters) if rm_titles else parameters,
        }
    else:
        raise ValueError("Model must be a Pydantic 2 model.")


class _SchemaConfig:
    """Configuration for the pydantic model.

    This is used to configure the pydantic model created from
    a function's signature.

    Parameters:
        extra: Whether to allow extra fields in the model.
        arbitrary_types_allowed: Whether to allow arbitrary types in the model.
            Defaults to True.
    """

    extra: str = "forbid"
    arbitrary_types_allowed: bool = True


FILTERED_ARGS = ("run_manager", "callbacks")


def create_schema_from_function(
    model_name: str,
    func: Callable,
    *,
    filter_args: Sequence[str] | None = None,
    include_injected: bool = True,
) -> type[BaseModel]:
    """Create a pydantic schema from a function's signature.

    Args:
        model_name: Name to assign to the generated pydantic schema.
        func: Function to generate the schema from.
        filter_args: Optional list of arguments to exclude from the schema.
            Defaults to FILTERED_ARGS.
        parse_docstring: Whether to parse the function's docstring for descriptions
            for each argument. Defaults to False.
        error_on_invalid_docstring: if ``parse_docstring`` is provided, configure
            whether to raise ValueError on invalid Google Style docstrings.
            Defaults to False.
        include_injected: Whether to include injected arguments in the schema.
            Defaults to True, since we want to include them in the schema
            when *validating* tool inputs.

    Returns:
        A pydantic model with the same arguments as the function.
    """
    sig = inspect.signature(func)

    with warnings.catch_warnings():
        # We are using deprecated functionality here.
        # This code should be re-written to simply construct a pydantic model
        # using inspect.signature and create_model.
        warnings.simplefilter("ignore", category=PydanticDeprecationWarning)
        validated = validate_arguments(func, config=_SchemaConfig)  # type: ignore
    # Let's ignore `self` and `cls` arguments for class and instance methods
    # If qualified name has a ".", then it likely belongs in a class namespace
    in_class = bool(func.__qualname__ and "." in func.__qualname__)

    has_args = False
    has_kwargs = False

    for param in sig.parameters.values():
        if param.kind == param.VAR_POSITIONAL:
            has_args = True
        elif param.kind == param.VAR_KEYWORD:
            has_kwargs = True

    inferred_model = validated.model  # type: ignore

    if filter_args:
        filter_args_: list[str] = list(filter_args)
    else:
        # Handle classmethods and instance methods
        existing_params: list[str] = list(sig.parameters.keys())
        if existing_params and existing_params[0] in ("self", "cls") and in_class:
            filter_args_ = [existing_params[0]] + list(FILTERED_ARGS)
        else:
            filter_args_ = list(FILTERED_ARGS)

        for existing_param in existing_params:
            if not include_injected and _is_injected_arg_type(sig.parameters[existing_param].annotation):
                filter_args_.append(existing_param)

    description, arg_descriptions = _infer_arg_descriptions(func)
    # Pydantic adds placeholder virtual fields we need to strip
    valid_properties = []
    for field in inferred_model.model_fields:
        if not has_args and field == "args":
            continue
        if not has_kwargs and field == "kwargs":
            continue

        if field == "v__duplicate_kwargs":  # Internal pydantic field
            continue

        if field not in filter_args_:
            valid_properties.append(field)

    return _create_subset_model(
        model_name,
        inferred_model,
        list(valid_properties),
        descriptions=arg_descriptions,
        fn_description=description,
    )


class InjectedToolArg:
    """Annotation for a Tool arg that is **not** meant to be generated by a model."""


def _is_injected_arg_type(type_: type, injected_type: type[InjectedToolArg] | None = None) -> bool:
    injected_type = injected_type or InjectedToolArg
    return any(
        isinstance(arg, injected_type) or (isinstance(arg, type) and issubclass(arg, injected_type))
        for arg in get_args(type_)[1:]
    )


def _infer_arg_descriptions(
    fn: Callable,
) -> tuple[str, dict]:
    """Infer argument descriptions from a function's docstring."""
    if hasattr(inspect, "get_annotations"):
        # This is for python < 3.10
        annotations = inspect.get_annotations(fn)  # type: ignore
    else:
        annotations = getattr(fn, "__annotations__", {})

    description = inspect.getdoc(fn) or ""
    arg_descriptions = {}
    for arg, arg_type in annotations.items():
        if arg in arg_descriptions:
            continue
        if desc := _get_annotation_description(arg_type):
            arg_descriptions[arg] = desc
    return description, arg_descriptions


def _is_annotated_type(typ: type[Any]) -> bool:
    return get_origin(typ) is Annotated


def _get_annotation_description(arg_type: type) -> str | None:
    if _is_annotated_type(arg_type):
        annotated_args = get_args(arg_type)
        for annotation in annotated_args[1:]:
            if isinstance(annotation, str):
                return annotation
    return None


def _create_subset_model(
    name: str,
    model: type[BaseModel],
    field_names: list[str],
    *,
    descriptions: dict | None = None,
    fn_description: str | None = None,
) -> type[BaseModel]:
    descriptions_ = descriptions or {}
    fields = {}
    for field_name in field_names:
        field = model.model_fields[field_name]  # type: ignore
        description = descriptions_.get(field_name, field.description)
        field_info = FieldInfo(description=description, default=field.default)
        if field.metadata:
            field_info.metadata = field.metadata
        fields[field_name] = (field.annotation, field_info)

    rtn = create_model(  # type: ignore
        name, **fields, __config__=ConfigDict(arbitrary_types_allowed=True)
    )

    selected_annotations = [
        (name, annotation) for name, annotation in model.__annotations__.items() if name in field_names
    ]

    rtn.__annotations__ = dict(selected_annotations)
    rtn.__doc__ = textwrap.dedent(fn_description or model.__doc__ or "")
    return rtn


def _rm_titles(kv: dict, prev_key: str = "") -> dict:
    new_kv = {}
    for k, v in kv.items():
        if k == "title":
            if isinstance(v, dict) and prev_key == "properties" and "title" in v:
                new_kv[k] = _rm_titles(v, k)
            else:
                continue
        elif isinstance(v, dict):
            new_kv[k] = _rm_titles(v, k)
        else:
            new_kv[k] = v
    return new_kv
