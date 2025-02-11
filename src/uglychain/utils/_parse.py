from __future__ import annotations

import json
import re

xml_not_json_regex = re.compile(r"^[^{]*<(\w+)>.*?<\/\w+>[^{]*$", re.DOTALL)
xml_param_regex = re.compile(r"<(\w+)>(.*?)</\1>", re.DOTALL)
json_regex = re.compile(r"(\{.*\})", re.MULTILINE | re.IGNORECASE | re.DOTALL)


def _parse_json(response: str) -> dict[str, str]:
    try:
        match = json_regex.search(response)
        if match:
            json_str = match.group()
            return json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format: {response}") from e


def parse_to_dict(response: str) -> dict[str, str]:
    if not response.strip():
        return {}
    if xml_not_json_regex.match(response):
        args = xml_param_regex.findall(response)
        if args:
            return {param: value for param, value in args}
        raise ValueError("Invalid XML format: {response}")
    else:
        try:
            return _parse_json(response)
        except ValueError as e:
            raise ValueError("No parameters found in response") from e
