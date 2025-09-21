"""
UglyChain 是一个用于构建大型语言模型（LLM）应用程序的框架。
它提供了一系列模块，用于配置、LLM交互、加载、规划、响应式代理、思维链以及工具集成。
"""

from __future__ import annotations

from .config import config  # 导入配置模块
from .console import BaseConsole  # 导入基础控制台模块
from .llm import llm  # 导入LLM模块
from .load import load  # 导入加载模块
from .plan import Plan  # 导入规划模块
from .react import react  # 导入响应式代理模块
from .think import think  # 导入思维链模块
from .tools import Tool, Tools  # 导入工具模块

# 定义对外暴露的模块和类
__all__ = ["config", "llm", "think", "react", "load", "Tools", "Tool", "BaseConsole", "Plan"]
# 定义UglyChain的版本
__version__ = "v1.6.6"
