from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from inspect import Parameter, signature

from pydantic import BaseModel, create_model


def json_post_endpoint(func: Callable) -> Callable:
    # 获取函数签名信息
    sig = signature(func)
    parameters = sig.parameters

    # 创建请求模型
    param_fields = {}
    for param_name, param in parameters.items():
        # 禁止可变参数
        if param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            raise TypeError(f"Function {func.__name__} cannot have *args/​**​kwargs")

        # 必须包含类型注解
        if param.annotation is Parameter.empty:
            raise TypeError(f"Parameter {param_name} must be type annotated")

        # 处理默认值
        default = ... if param.default is Parameter.empty else param.default
        param_fields[param_name] = (param.annotation, default)

    RequestModel: type[BaseModel] = create_model(f"{func.__name__}_Request", **param_fields)  # noqa: N806

    @wraps(func)
    async def wrapper(request: RequestModel):  # type: ignore
        return func(**request.model_dump())  # type: ignore[attr-defined]

    return append_to_signature(
        wrapper, inspect.Parameter("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=RequestModel)
    )


def append_to_signature(func: Callable, *params: inspect.Parameter) -> Callable:
    func.__signature__ = inspect.Signature(parameters=params)  # type: ignore[attr-defined]
    return func
