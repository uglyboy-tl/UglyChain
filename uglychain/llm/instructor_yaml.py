import json
import re
from functools import wraps
from typing import Type

from loguru import logger
from pydantic import BaseModel, ValidationError, create_model
from pydantic_yaml import parse_yaml_raw_as

PYDANTIC_FORMAT_INSTRUCTIONS = """The output must be a YAML object , according to the following schema:
=====
{schema}
=====


As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
the object ```yaml\nfoo:\n- bar\n- baz\n``` is a well-formatted instance of the schema.


Answer:
```yaml\
"""


class ParseError(Exception):
    pass


class Instructor(BaseModel):
    @classmethod
    def from_response(cls, response: str) -> "Instructor":
        try:
            match = re.search(r"```yaml(.*?)(```|$)", response.strip(), re.IGNORECASE | re.DOTALL)
            yaml_str = response.strip()
            if yaml_str.endswith("```"):
                yaml_str = yaml_str[:-3]
            if match:
                yaml_str = match.group(1).strip()
            logger.trace(f"yaml_str: {yaml_str}")
            return parse_yaml_raw_as(cls, yaml_str)

        except (json.JSONDecodeError, ValidationError) as e:
            name = cls.__name__
            msg = f"Failed to parse {name} from completion {response}. Got: {e}"
            raise ParseError(msg) from e

    @classmethod
    def get_format_instructions(cls) -> str:
        schema = cls.model_json_schema()

        # Remove extraneous fields.
        reduced_schema = schema
        if "title" in reduced_schema:
            del reduced_schema["title"]
        if "type" in reduced_schema:
            del reduced_schema["type"]
        # Ensure json in context is well-formed with double quotes.
        schema_str = json.dumps(reduced_schema, ensure_ascii=False)

        return PYDANTIC_FORMAT_INSTRUCTIONS.format(schema=schema_str)

    @classmethod
    def from_BaseModel(cls, cls1) -> Type["Instructor"]:
        if not issubclass(cls1, BaseModel):
            raise TypeError("Class must be a subclass of pydantic.BaseModel")

        return wraps(cls1, updated=())(
            create_model(
                cls1.__name__,
                __base__=(cls1, Instructor),  # type: ignore
            )
        )
