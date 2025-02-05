from __future__ import annotations

import ast
import re

xml_param_regex = re.compile(r"<(\w+)>(.*?)</\1>", re.DOTALL)
json_regex = re.compile(r"(\{.*\})", re.MULTILINE | re.IGNORECASE | re.DOTALL)


def _parse_json(response: str) -> dict[str, str]:
    match = json_regex.search(response)
    if match:
        json_str = match.group()
        try:
            args = ast.literal_eval(json_str)
            return args
        except Exception as e:
            raise ValueError("Invalid JSON format") from e
    else:
        raise ValueError("No JSON found in response")


def parse_to_dict(response: str) -> dict[str, str]:
    args = {param: value for param, value in xml_param_regex.findall(response)}
    if not args:
        try:
            args = _parse_json(response)
        except ValueError as e:
            raise ValueError("No parameters found in response") from e
    return args
