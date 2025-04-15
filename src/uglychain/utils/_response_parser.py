from __future__ import annotations

import json
import re
from ast import literal_eval

xml_not_json_regex = re.compile(r"^[^{]*<(\w+)>.*?<\/\w+>[^{]*$", re.DOTALL)
xml_param_regex = re.compile(r"<(\w+)>(.*?)</\1>", re.DOTALL)
json_regex = re.compile(r"(\{.*\})", re.MULTILINE | re.IGNORECASE | re.DOTALL)


def extract_json_dict(response: str) -> dict[str, object]:
    try:
        match = json_regex.search(response)
        if match:
            json_str = match.group()
            parsed_dict = json.loads(json_str)
            # Convert values to appropriate types
            return {k: infer_value_type(v) if isinstance(v, str) else v for k, v in parsed_dict.items()}
        else:
            raise ValueError("No JSON found in response")
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format: {response}") from e


def infer_value_type(value: str) -> object:
    """Convert string value to appropriate type (number, boolean, list) if possible."""
    # Preserve the original value
    original_value = value

    # Use a stripped version for pattern matching
    stripped_value = value.strip()

    # Check for boolean
    if stripped_value.lower() == "true":
        return True
    if stripped_value.lower() == "false":
        return False

    # Try to convert to number or list using literal_eval
    try:
        # Check if it looks like a number, list, tuple, or dict before attempting conversion
        if (
            re.match(r"^-?\d+(\.\d+)?$", stripped_value)  # number
            or (stripped_value.startswith("[") and stripped_value.endswith("]"))  # list
            or (stripped_value.startswith("(") and stripped_value.endswith(")"))  # tuple
            or (stripped_value.startswith("{") and stripped_value.endswith("}"))
        ):  # dict
            return literal_eval(stripped_value)
    except (ValueError, SyntaxError):
        pass

    # Return original value if no conversion applies
    return original_value


def parse_response_to_dict(response: str) -> dict[str, object]:
    if not response.strip():
        return {}
    if xml_not_json_regex.match(response):
        args = xml_param_regex.findall(response)
        if args:
            return {param: infer_value_type(value) for param, value in args}
        raise ValueError("Invalid XML format: {response}")
    else:
        try:
            return extract_json_dict(response)
        except ValueError as e:
            raise ValueError("No parameters found in response") from e
