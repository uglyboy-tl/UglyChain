from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Iterator
from functools import partial
from pathlib import Path
from typing import Any

from .llm import llm
from .schema import P, ToolResponse
from .utils._load_utils import YAML_INSTANCE, convert_to_variable_name, resolve_references, update_dict_recursively

# Constants
PROMPT_PATTERN = re.compile(r"-{3,}\n(.*)-{3,}\n(.*)", re.DOTALL)
PLACEHOLDER_PATTERN = re.compile(r"(?<!{){([^{}\n]+)}(?!})")


def load(
    path_str: str, **kwargs: Any
) -> Callable[..., str | Iterator[str] | ToolResponse | list[str] | list[ToolResponse]]:
    """Load a prompt template from a file and return a function that generates prompts.

    The prompt file should be in markdown format with two parts:
    1. YAML frontmatter: Contains configuration like model, name, description etc.
    2. Prompt template: Contains the actual prompt template with placeholders.

    Args:
        path_str: Path to the prompt template file
        **kwargs: Additional configuration to override the YAML frontmatter

    Returns:
        A function that takes the template variables as arguments and returns the generated prompt

    Raises:
        ValueError: If the prompt file format is invalid
        FileNotFoundError: If the prompt file does not exist
    """
    path = Path(path_str)

    content = path.read_text(encoding="utf-8")
    result = PROMPT_PATTERN.search(content)
    if not result:
        raise ValueError(
            "Illegal formatting of prompt file. The file should be in markdown format with two parts:\n"
            "1. YAML frontmatter between --- markers\n"
            "2. Prompt template in YAML format"
        )
    config_content, prompt_template = result.groups()
    # 处理 config_content
    configs = YAML_INSTANCE.load(config_content)
    if not isinstance(configs, dict):
        raise ValueError("YAML frontmatter must be a dictionary.")
    configs = resolve_references(configs, base_path=path.parent)
    configs = update_dict_recursively(configs, resolve_references(kwargs, base_path=path.parent))  # type: ignore

    ## 从配置文件中解析出name, description, model, map_keys 等信息
    name = convert_to_variable_name(configs.pop("name", path.name))
    for key in ["id", "description", "author", "version", "tags"]:
        if key not in configs:
            continue
        configs.pop(key)
    model = configs.pop("model", "")
    map_keys: list[str] | None = configs.pop("map_keys", None)

    # 处理 prompt_template
    system_prompt, user_prompt_template = _parse_prompt_template(prompt_template)
    inputs = PLACEHOLDER_PATTERN.findall(user_prompt_template)
    parameters = []
    for input in inputs:
        parameters.append(inspect.Parameter(input, inspect.Parameter.POSITIONAL_OR_KEYWORD))
    new_sig = inspect.Signature(parameters)

    def func(*args: P.args, **kwargs: P.kwargs) -> str:
        for i, arg in enumerate(args):
            kwargs[inputs[i]] = arg
        _replace = partial(_replace_placeholder, kwargs=kwargs)

        result = PLACEHOLDER_PATTERN.sub(_replace, user_prompt_template)
        return result

    if name:
        func.__name__ = name
    func.__doc__ = system_prompt
    func.__signature__ = new_sig  # type: ignore
    # return func
    return llm(model, response_format=None, map_keys=map_keys, **configs)(func)


def _replace_placeholder(match: re.Match[str], kwargs: dict[str, Any]) -> str:
    key = match.group(1)
    value = kwargs.get(key, match.group(0))
    return value


def _parse_prompt_template(prompt_template: str) -> tuple[str, str]:
    """Parse a prompt template into system prompt and user prompt.

    Args:
        prompt_template: The prompt template string in YAML format

    Returns:
        A tuple of (system_prompt, user_prompt_template)

    Raises:
        ValueError: If the prompt template format is invalid or missing required fields
    """
    message = YAML_INSTANCE.load(prompt_template)
    if isinstance(message, str):
        return "", message
    elif isinstance(message, dict):
        if len(message) == 1 and "user" not in message and next(iter(message.values())) is None:
            return "", prompt_template
        for key in message:
            if key == "system":
                system_prompt = message[key]
                break
        else:
            system_prompt = ""
        try:
            user_prompt_template = message["user"]
        except KeyError as e:
            raise ValueError("Prompt template must contain a 'user' field.") from e
        return system_prompt, user_prompt_template
    else:
        raise ValueError(
            "Prompt template must be either a string (user prompt) or a dictionary with 'user' field."
        ) from None
