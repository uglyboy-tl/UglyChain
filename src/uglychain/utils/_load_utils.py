"""Utility functions for loading and processing configuration files."""

from __future__ import annotations

import json
import os
import re
from functools import singledispatch
from os import PathLike
from pathlib import Path
from typing import IO, Any, AnyStr

from ruamel.yaml import YAML, YAMLError

# Constants
YAML_INSTANCE = YAML()
YAML_INSTANCE.preserve_quotes = True

REFERENCE_PATTERN = re.compile(r"\$\{(\w+):(.*)\}")


def resolve_file_path(path: str | Path, base_path: str | Path | None = None) -> Path:
    """Resolve a file path, optionally relative to a base path.

    Args:
        path: The path to resolve
        base_path: Optional base path to resolve relative paths against

    Returns:
        The resolved Path object

    Raises:
        FileNotFoundError: If the resolved path does not exist
    """
    path_obj = Path(path)
    if not path_obj.is_absolute() and base_path is not None:
        path_obj = Path(base_path) / path_obj

    if not path_obj.exists():
        raise FileNotFoundError(f"Cannot find file: {path}")

    return path_obj


def update_dict_recursively(origin_dict: dict[str, Any], overwrite_dict: dict[str, Any]) -> dict[str, Any]:
    """Recursively update a dictionary with values from another dictionary.

    Args:
        origin_dict: The original dictionary to update
        overwrite_dict: The dictionary containing values to overwrite with

    Returns:
        A new dictionary containing the merged values
    """
    updated_dict: dict[str, Any] = {}
    for k, v in overwrite_dict.items():
        if isinstance(v, dict):
            updated_dict[k] = update_dict_recursively(origin_dict.get(k, {}), v)
        else:
            updated_dict[k] = v
    for k, v in origin_dict.items():
        if k not in updated_dict:
            updated_dict[k] = v
    return updated_dict


@singledispatch
def resolve_references(origin: Any, base_path: str | Path | None = None) -> Any:
    """Resolve all references in the object recursively.

    Args:
        origin: The object to resolve references in
        base_path: Optional base path for resolving file references

    Returns:
        The object with all references resolved
    """
    return origin


@resolve_references.register(str)
def _(origin: str, base_path: str | Path | None = None) -> str:
    return resolve_reference(origin, base_path=base_path)


@resolve_references.register(list)
def _(origin: list, base_path: str | Path | None = None) -> list:
    return [resolve_references(item, base_path=base_path) for item in origin]


@resolve_references.register(dict)
def _(origin: dict, base_path: str | Path | None = None) -> dict:
    return {key: resolve_references(value, base_path=base_path) for key, value in origin.items()}


def resolve_reference(reference: str, base_path: str | Path | None = None) -> Any:
    """Resolve a reference string to its actual value.

    Supports two types of references:
    - Environment variables: ${env:ENV_NAME}
    - File references: ${file:file_path}

    Args:
        reference: The reference string to resolve
        base_path: Optional base path for resolving file references

    Returns:
        The resolved value

    Raises:
        FileNotFoundError: If a referenced file cannot be found
        YAMLError: If a referenced YAML file is invalid
    """
    match = REFERENCE_PATTERN.match(reference)
    if match:
        reference_type, value = match.groups()
        if reference_type == "env":
            return os.environ.get(value, reference)
        elif reference_type == "file":
            path = resolve_file_path(value, base_path)
            with path.open("r") as f:
                if path.suffix.lower() == ".json":
                    return json.load(f)
                elif path.suffix.lower() in [".yml", ".yaml"]:
                    return load_yaml(f)
                else:
                    return f.read()
        else:
            # logger.warning(f"Unknown reference type {reference_type}, return original value {reference}.")
            return reference
    else:
        return reference


def load_yaml(source: AnyStr | PathLike | IO | None) -> dict[str, Any]:
    """Load a YAML file or stream into a dictionary.

    Args:
        source: Path to YAML file, file-like object, or None

    Returns:
        Dictionary containing the YAML contents

    Raises:
        FileNotFoundError: If the YAML file cannot be found
        PermissionError: If the file/stream is not readable
        YAMLError: If the YAML content is invalid
    """
    if source is None:
        return {}

    # pylint: disable=redefined-builtin
    input = None
    must_open_file = False
    try:  # check source type by duck-typing it as an IOBase
        readable = source.readable()  # type: ignore
        if not readable:  # source is misformatted stream or file
            msg = "File Permissions Error: The already-open \n\n inputted file is not readable."
            raise PermissionError(msg)
        # source is an already-open stream or file, we can read() from it directly.
        input = source
    except AttributeError:
        # source has no writable() function, assume it's a string or file path.
        must_open_file = True

    if must_open_file:  # If supplied a file path, open it.
        try:
            input = Path(source).open(encoding="utf-8")  # type: ignore
        except OSError as e:  # FileNotFoundError introduced in Python 3
            raise FileNotFoundError(f"No such file or directory: {source!r}") from e
    # input should now be a readable file or stream. Parse it.
    try:
        cfg = YAML_INSTANCE.load(input)
    except YAMLError as e:
        msg = f"Error while parsing yaml file: {source!r} \n\n {str(e)}"
        raise YAMLError(msg) from e
    finally:
        if must_open_file:
            input.close()  # type: ignore
    if cfg is None:
        return {}
    return cfg


def convert_to_variable_name(name: str) -> str:
    """Convert a string to a valid Python variable name.

    This function performs two transformations:
    1. Replaces all spaces with underscores
    2. Converts the string to lowercase

    Args:
        name: The string to convert

    Returns:
        A string that can be used as a valid Python variable name

    Examples:
        >>> convert_to_variable_name("Hello World")
        'hello_world'
        >>> convert_to_variable_name("Multiple   Spaces")
        'multiple___spaces'
        >>> convert_to_variable_name("UPPERCASE")
        'uppercase'
    """
    return name.replace(" ", "_").lower()
