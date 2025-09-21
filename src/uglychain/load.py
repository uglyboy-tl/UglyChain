"""
load模块提供了从文件加载提示模板的功能。
支持YAML格式的配置文件，可以定义模型、参数和提示模板，
并自动生成可调用的LLM函数。
"""

from __future__ import annotations

import inspect  # 导入inspect模块，用于检查和操作函数签名
import re  # 导入re模块，用于正则表达式匹配
from collections.abc import Callable, Iterator  # 导入抽象基类，用于类型提示
from functools import partial  # 导入partial，用于创建偏函数
from pathlib import Path  # 导入Path类，用于文件路径操作
from typing import Any  # 导入Any类型，用于类型提示

from .llm import llm  # 从当前包导入llm装饰器
from .schema import P, ToolResponse  # 从当前包导入P和ToolResponse类型
from .session import Session  # 从当前包导入Session类
from .utils._load_utils import (  # 导入加载工具函数
    YAML_INSTANCE,
    convert_to_variable_name,
    resolve_references,
    update_dict_recursively,
)

# 常量定义
PROMPT_PATTERN = re.compile(r"-{3,}\n(.*)-{3,}\n(.*)", re.DOTALL)  # 匹配YAML frontmatter的正则表达式
PLACEHOLDER_PATTERN = re.compile(r"(?<!{){([^{}\n]+)}(?!})")  # 匹配占位符的正则表达式


def load(
    path_str: str, **kwargs: Any
) -> Callable[..., str | Iterator[str] | ToolResponse | list[str] | list[ToolResponse]]:
    """
    从文件加载提示模板并返回一个生成提示的函数。

    提示文件应该是markdown格式，包含两个部分：
    1. YAML前置内容：包含模型、名称、描述等配置信息
    2. 提示模板：包含实际的提示模板和占位符

    Args:
        path_str: 提示模板文件的路径
        **kwargs: 用于覆盖YAML前置内容的额外配置

    Returns:
        一个函数，接受模板变量作为参数并返回生成的提示

    Raises:
        ValueError: 如果提示文件格式无效
        FileNotFoundError: 如果提示文件不存在
    """
    path = Path(path_str)  # 创建Path对象

    # 读取文件内容
    content = path.read_text(encoding="utf-8")
    result = PROMPT_PATTERN.search(content)  # 搜索YAML前置内容和模板
    if not result:
        raise ValueError(
            "Illegal formatting of prompt file. The file should be in markdown format with two parts:\n"
            "1. YAML frontmatter between --- markers\n"
            "2. Prompt template in YAML format"
        )
    config_content, prompt_template = result.groups()  # 分离配置内容和提示模板

    # 处理配置内容
    configs = YAML_INSTANCE.load(config_content)  # 解析YAML配置
    if not isinstance(configs, dict):
        raise ValueError("YAML frontmatter must be a dictionary.")
    configs = resolve_references(configs, base_path=path.parent)  # 解析配置中的引用
    configs = update_dict_recursively(configs, resolve_references(kwargs, base_path=path.parent))  # type: ignore  # 合并传入的配置

    # 从配置文件中解析出name, description, model, map_keys等信息
    name = convert_to_variable_name(configs.pop("name", path.name))  # 获取函数名称
    session = Session()  # 创建会话对象
    for key in ["id", "description", "author", "version", "tags"]:
        value = configs.pop(key, None)
        if value:
            session.info[key] = value  # 设置会话信息

    model = configs.pop("model", "")  # 获取模型名称
    map_keys: list[str] | None = configs.pop("map_keys", None)  # 获取映射键

    # 处理提示模板
    system_prompt, user_prompt_template = _parse_prompt_template(prompt_template)  # 解析提示模板
    inputs = PLACEHOLDER_PATTERN.findall(user_prompt_template)  # 查找所有占位符
    parameters = []
    # 为每个占位符创建函数参数
    for input in inputs:
        parameters.append(inspect.Parameter(input, inspect.Parameter.POSITIONAL_OR_KEYWORD))
    new_sig = inspect.Signature(parameters)  # 创建新的函数签名

    def func(*args: P.args, **kwargs: P.kwargs) -> str:
        """
        动态生成的函数，用于填充提示模板。

        Args:
            *args: 位置参数，对应模板中的占位符
            **kwargs: 关键字参数，对应模板中的占位符

        Returns:
            填充后的提示字符串
        """
        # 将位置参数转换为关键字参数
        for i, arg in enumerate(args):
            kwargs[inputs[i]] = arg
        # 创建占位符替换函数
        _replace = partial(_replace_placeholder, kwargs=kwargs)

        # 替换模板中的占位符
        result = PLACEHOLDER_PATTERN.sub(_replace, user_prompt_template)
        return result

    if name:
        func.__name__ = name  # 设置函数名称
    func.__doc__ = system_prompt  # 设置函数文档字符串为系统提示
    func.__signature__ = new_sig  # type: ignore  # 设置函数签名

    # 使用llm装饰器包装函数
    return llm(model, response_format=None, map_keys=map_keys, session=session, **configs)(func)


def _replace_placeholder(match: re.Match[str], kwargs: dict[str, Any]) -> str:
    """
    替换占位符的辅助函数。

    Args:
        match: 正则表达式匹配对象
        kwargs: 包含替换值的字典

    Returns:
        替换后的字符串，如果找不到对应的值则返回原始占位符
    """
    key = match.group(1)  # 获取占位符键名
    value = kwargs.get(key, match.group(0))  # 获取对应的值，如果不存在则返回原始匹配
    return value


def _parse_prompt_template(prompt_template: str) -> tuple[str, str]:
    """
    解析提示模板为系统提示和用户提示。

    Args:
        prompt_template: YAML格式的提示模板字符串

    Returns:
        包含系统提示和用户提示模板的元组

    Raises:
        ValueError: 如果提示模板格式无效或缺少必需字段
    """
    message = YAML_INSTANCE.load(prompt_template)  # 解析YAML内容
    if isinstance(message, str):
        # 如果是字符串，则作为用户提示，没有系统提示
        return "", message
    elif isinstance(message, dict):
        # 如果是字典，则分别处理系统提示和用户提示
        if len(message) == 1 and "user" not in message and next(iter(message.values())) is None:
            return "", prompt_template
        # 查找系统提示
        for key in message:
            if key == "system":
                system_prompt = message[key]
                break
        else:
            system_prompt = ""
        try:
            # 获取用户提示模板
            user_prompt_template = message["user"]
        except KeyError as e:
            raise ValueError("Prompt template must contain a 'user' field.") from e
        return system_prompt, user_prompt_template
    else:
        raise ValueError(
            "Prompt template must be either a string (user prompt) or a dictionary with 'user' field."
        ) from None
