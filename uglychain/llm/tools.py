import inspect
from enum import Enum
from typing import Callable, List, Literal, Union, cast, get_args, get_origin

from docstring_parser import parse
from pydantic import BaseModel, Field


class FunctionCall(BaseModel):
    name: str = Field(..., description="tool name")
    args: dict = Field(..., description="tool arguments")


class ActionResopnse(BaseModel):
    thought: str = Field(..., description="Think step by step and explan why you need to use a tool")
    action: FunctionCall = Field(..., description="The action to take")


def finish(answer: str) -> str:
    """When get Final Answer, use this tool to return the answer and finishes the task.
    Args:
        answer (str): The response to return.
    """
    return answer


def run_function(tools: List[Callable], response: FunctionCall):
    for tool in tools:
        if tool.__name__ == response.name:
            return tool(**response.args)
    raise ValueError(f"Can't find tool {response.name}")


FUNCTION_CALL_FORMAT = """
-----
You can use tools: [{tool_names}]

Respond with tool name and tool arguments to achieve the instruction:

{tool_schema}
"""

FUNCTION_CALL_WITH_FINISH_FORMAT = """
-----
You can use tools: [{tool_names}]

Respond with tool name and tool arguments to achieve the instruction. if you can respond directly, use the tool 'finish' to return the answer and finishes the task:

{tool_schema}
"""


def to_json_schema_type(type_name: str) -> str:
    type_map = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "None": "null",
        "Any": "any",
        "Dict": "object",
        "List": "array",
        "Optional": "any",
    }
    return type_map.get(type_name, "any")


def parse_annotation(annotation):
    if getattr(annotation, "__origin__", None) == Union:
        types = [t.__name__ if t.__name__ != "NoneType" else "None" for t in annotation.__args__]
        return to_json_schema_type(types[0])
    elif get_origin(annotation) is Literal:
        return "enum", list(get_args(annotation))
    elif issubclass(annotation, Enum):  # If the annotation is an Enum type
        return "enum", [item.name for item in annotation]  # Return 'enum' and a list of the names of the enum members
    elif getattr(annotation, "__origin__", None) is not None:
        if annotation._name is not None:
            return f"{to_json_schema_type(annotation._name)}[{','.join([to_json_schema_type(i.__name__) for i in annotation.__args__])}]"
        else:
            return f"{to_json_schema_type(annotation.__origin__.__name__)}[{','.join([to_json_schema_type(i.__name__) for i in annotation.__args__])}]"
    else:
        return to_json_schema_type(annotation.__name__)


def get_pydantic_schema(pydantic_obj: BaseModel, visited_models=None) -> dict:
    if visited_models is None:
        visited_models = set()

    if pydantic_obj in visited_models:
        raise ValueError(f"Circular reference detected: {pydantic_obj.__name__}")

    visited_models.add(pydantic_obj)

    schema = pydantic_obj.model_json_schema()
    definitions = schema.pop("definitions", {})

    def resolve_schema(schema):
        if "$ref" in schema:
            ref_path = schema["$ref"]
            definition_key = ref_path.split("/")[-1]
            return resolve_schema(definitions[definition_key])
        elif "items" in schema:
            schema["items"] = resolve_schema(schema["items"])
        return schema

    schema = resolve_schema(schema)
    for name, property in schema["properties"].items():
        schema["properties"][name] = resolve_schema(property)

    visited_models.remove(pydantic_obj)

    return schema


def function_schema(func: Callable):
    signature = inspect.signature(func)
    docstring = inspect.getdoc(func)
    if docstring:
        docstring_parsed = parse(docstring)
    else:
        docstring_parsed = parse("")

    parameters = {}
    required = []

    for name, param in signature.parameters.items():
        json_type = parse_annotation(param.annotation)
        param_info = None

        if isinstance(param.annotation, type) and issubclass(param.annotation, BaseModel):
            # If the parameter is a Pydantic object
            # val_func = validate_arguments(func)
            param_info = get_pydantic_schema(cast(BaseModel, param.annotation))
            param_info["description"] = param.annotation.__doc__
            # Add Pydantic object parameter to the required list
            required.append(name)
        elif isinstance(json_type, tuple) and json_type[0] == "enum":  # If the type is an Enum
            param_info = {
                "type": "string",
                "enum": json_type[1],  # Add an 'enum' field with the names of the enum members
                "description": "",
            }
        else:
            param_info = {"type": json_type, "description": ""}

        if json_type != "any" and name != "self" and param.default == inspect.Parameter.empty:
            required.append(name)

        for doc_param in docstring_parsed.params:
            if doc_param.arg_name == name:
                param_info["description"] = doc_param.description if doc_param.description else ""

        parameters[name] = param_info

    function_info = {
        "name": func.__name__,
        "description": docstring_parsed.short_description,
        "parameters": {
            "type": "object",
            "properties": parameters,
            "required": required,
        },
    }

    return function_info


def tools_schema(tools: List[Callable]):
    tools_schema = []

    for tool in tools:
        tool_schema = {"type": "function", "function": function_schema(tool)}
        tools_schema.append(tool_schema)
    return tools_schema
