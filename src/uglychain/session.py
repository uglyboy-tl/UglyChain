"""
session模块提供会话管理和日志记录功能。

该模块定义了Session类，用于管理不同类型的会话（llm、think、react），
并提供了日志记录和消息传递的功能。
"""

from __future__ import annotations

import inspect  # 用于检查函数签名
import logging  # 用于日志记录
import sys  # 用于检测运行环境
import uuid  # 用于生成唯一标识符
from collections.abc import Callable  # 用于类型提示
from dataclasses import dataclass, field  # 用于数据类定义
from datetime import datetime  # 用于时间戳生成
from pathlib import Path  # 用于路径操作
from typing import Any, ClassVar, Literal  # 用于类型提示

from .config import config  # 导入配置
from .console import BaseConsole, SimpleConsole  # 导入控制台类
from .utils import MessageBus  # 导入消息总线

# 函数调用格式化的常量
MAX_AGRS: int = 5  # 显示的最大参数数量
MAX_ARGS_LEN: int = 8  # 参数值的最大长度


class CustomFormatter(logging.Formatter):
    """
    自定义日志格式化器，根据是否有消息内容调整格式。
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        根据日志记录是否包含消息来格式化日志。

        Args:
            record: 日志记录对象

        Returns:
            str: 格式化后的日志字符串
        """
        if not record.msg:
            self._style._fmt = "%(asctime)s - %(id)s - %(module_name)s"
        else:
            self._style._fmt = "%(asctime)s - %(id)s - %(module_name)s - %(message)s"
        return super().format(record)


@dataclass
class Logger:
    """
    会话日志记录器，用于记录会话相关的日志信息。
    """

    _logger: ClassVar[logging.Logger | None] = None  # 类变量，存储日志记录器实例

    @classmethod
    def info(cls, message: str, **kwargs: Any) -> None:
        """
        记录信息级别的日志。

        Args:
            message: 日志消息
            **kwargs: 额外的日志信息
        """
        # 在测试环境中不记录日志
        if "pytest" in sys.modules:
            return

        # 如果会话日志功能被禁用，则不记录
        if not config.session_log:
            return

        # 懒加载日志记录器
        if cls._logger is None:
            cls._logger = logging.getLogger("SessionLogger")
            cls._logger.setLevel(logging.INFO)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            Path("logs").mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(f"logs/session_{timestamp}.log")
            handler.setFormatter(CustomFormatter())
            cls._logger.addHandler(handler)
        cls._logger.info(message, **kwargs)


@dataclass
class Session:
    """
    会话类，管理不同类型的会话（llm、think、react）。

    提供消息传递、日志记录和控制台管理功能。
    """

    session_type: Literal["llm", "think", "react"] = "llm"  # 会话类型
    uuid: uuid.UUID = field(init=False, default_factory=uuid.uuid4)  # 会话唯一标识符
    info: dict[str, str] = field(init=False, default_factory=dict)  # 会话信息
    consoles: list[BaseConsole] = field(init=False, default_factory=list)  # 控制台列表

    def __post_init__(self) -> None:
        """初始化后添加默认控制台"""
        self.add_console(SimpleConsole)

    def add_console(self, cls: type[BaseConsole]) -> None:
        """
        添加控制台到会话。

        Args:
            cls: 控制台类
        """
        console = cls(self.id)
        self.console_register(console)

    def console_register(self, console: BaseConsole) -> None:
        """
        注册控制台到会话，并设置消息总线。

        根据会话类型注册不同的消息处理器。

        Args:
            console: 控制台实例
        """
        self.consoles.append(console)
        MessageBus.get(self.id, "base_info").regedit(console.base_info)
        MessageBus.get(self.id, "messages").regedit(console.messages)
        if self.session_type == "llm":
            # LLM会话特有的消息处理器
            MessageBus.get(self.id, "api_params").regedit(console.api_params)
            MessageBus.get(self.id, "results").regedit(console.results)
            MessageBus.get(self.id, "progress_start").regedit(console.progress_start)
            MessageBus.get(self.id, "progress_intermediate").regedit(console.progress_intermediate)
            MessageBus.get(self.id, "progress_end").regedit(console.progress_end)
        elif self.session_type == "think":
            # 思维链会话特有的消息处理器
            MessageBus.get(self.id, "api_params").regedit(console.api_params)
            MessageBus.get(self.id, "results").regedit(console.results)
        elif self.session_type == "react":
            # ReAct会话特有的消息处理器
            MessageBus.get(self.id, "rule").regedit(console.rule)
            MessageBus.get(self.id, "action").regedit(console.action_info)
            MessageBus.get(self.id, "tool").regedit(console.tool_info)

    @property
    def model(self) -> str:
        """获取会话使用的模型名称"""
        return self.info.get("model", "")

    @model.setter
    def model(self, model: str) -> None:
        """设置会话使用的模型名称"""
        self.info["model"] = model

    @property
    def func(self) -> str:
        """获取会话关联的函数名称"""
        return self.info.get("func", "")

    @func.setter
    def func(self, func: str) -> None:
        """设置会话关联的函数名称（仅在未设置时）"""
        if "func" not in self.info:
            self.info["func"] = func

    @property
    def id(self) -> str:
        """获取会话ID，优先使用info中的id，否则使用UUID"""
        id = self.info.get("id")
        if id:
            return id
        else:
            return self.uuid.hex

    def send(self, module: str, message: Any = None, /, **kwargs: Any) -> None:
        """
        发送消息到指定模块。

        Args:
            module: 目标模块名称
            message: 消息内容
            **kwargs: 额外的消息参数
        """
        # 记录日志
        if config.session_log:
            Logger.info(message, extra={"id": self.id, "module_name": module, "kwargs": kwargs})
        # 发送消息
        MessageBus.get(self.id, module).send(message, **kwargs)

    def show_base_info(self) -> None:
        """显示会话基本信息，并禁用后续的基本信息显示"""
        self.send("base_info", self.func, model=self.model)
        for console in self.consoles:
            console.show_base_info = False

    def call_tool_confirm(self, name: str) -> bool:
        """
        确认是否调用工具。

        Args:
            name: 工具名称

        Returns:
            bool: 是否确认调用
        """
        return self.consoles[0].call_tool_confirm(name)

    @staticmethod
    def format_func_call(func: Callable, *args: Any, **kwargs: Any) -> str:
        """
        格式化函数调用为字符串表示。

        Args:
            func: 被调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            str: 格式化后的函数调用字符串
        """
        # 获取函数的参数信息
        signature = inspect.signature(func)
        bound_arguments = signature.bind(*args, **kwargs)
        bound_arguments.apply_defaults()

        # 构建参数字符串
        args_str = []
        for name, value in bound_arguments.arguments.items():
            if isinstance(value, list | dict | set | tuple):
                end_str = ""
                display_value = ""
                if len(value) > 2:
                    end_str = ",..."
                if isinstance(value, dict):
                    display_value = f"{{{', '.join([f'{_format_arg_str(k)}: {_format_arg_str(value[k])}' for k in list(value)[:2]])}{end_str}}}"
                elif isinstance(value, tuple):
                    display_value = f"({', '.join([_format_arg_str(i) for i in value[:2]])}{end_str})"
                elif isinstance(value, set):
                    display_value = f"{{{', '.join([_format_arg_str(i) for i in list(value)[:2]])}{end_str}}}"
                elif isinstance(value, list):
                    display_value = f"[{', '.join([_format_arg_str(i) for i in value[:2]])}{end_str}]"
                args_str.append(f"{name}={display_value}")
            else:
                args_str.append(f"{name}={_format_arg_str(value)}")

        # 构建最终的函数调用字符串
        if len(args_str) <= MAX_AGRS:
            func_call_str = f"{func.__name__}({', '.join(args_str)})"
        else:
            func_call_str = f"{func.__name__}({', '.join(args_str[:MAX_AGRS])}, ...)"
        return func_call_str


def _format_arg_str(arg_str: Any, max_len: int = MAX_ARGS_LEN) -> str:
    """
    格式化参数值为字符串表示。

    Args:
        arg_str: 参数值
        max_len: 最大长度

    Returns:
        str: 格式化后的参数字符串
    """
    if isinstance(arg_str, str):
        if len(arg_str) > max_len:
            return f"'{arg_str[:max_len].strip()}...'"
        else:
            return f"'{arg_str}'"
    else:
        arg_str = repr(arg_str)
        if len(arg_str) > max_len:
            return f"{arg_str[:max_len].strip()}..."
        else:
            return arg_str
