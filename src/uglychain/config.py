"""
配置模块，用于管理UglyChain的全局配置设置。
支持从配置文件读取配置，并提供了默认配置值。
"""

from __future__ import annotations

import configparser  # 导入configparser模块，用于解析INI格式的配置文件
import json  # 导入json模块，用于解析JSON格式的配置值
import os  # 导入os模块，用于访问环境变量和文件系统
from pathlib import Path  # 导入Path类，用于处理文件路径
from typing import Any  # 导入Any类型，用于类型提示

from pydantic import BaseModel, Field  # 导入Pydantic的BaseModel和Field，用于数据验证和配置管理

# 读取本地配置文件以覆盖默认值
CONFIG_FILENAME = "config.ini"  # 配置文件名
CONFIG_APP_DIR = "uglychain"  # 应用配置目录名
CONFIG_SECTION = "DEFAULT"  # 配置文件中的默认节名


class Config(BaseModel):
    """
    配置类，继承自Pydantic的BaseModel，用于管理UglyChain的配置设置。
    支持从INI配置文件读取配置值，并提供了合理的默认值。
    """

    default_model: str = Field(default="openai:gpt-4o-mini", description="默认语言模型。")
    default_api_params: dict[str, Any] = Field(default_factory=dict, description="语言模型的默认参数。")
    default_language: str = Field(default="Chinese", description="默认语言。")
    response_markdown_type: str = Field(default="yaml", description="默认的markdown类型。")
    llm_max_retry: int = Field(default=3, description="语言模型的最大重试次数。")
    llm_timeout: int = Field(default=30, description="语言模型的最大运行时间（秒）。")
    llm_wait_time: int = Field(default=0, description="语言模型的每次重试等待时间（秒）。")
    use_parallel_processing: bool = Field(default=False, description="是否对语言模型使用并行处理。")
    session_log: bool = Field(default=True, description="如果为真，则启用会话日志记录。")
    verbose: bool = Field(default=False, description="如果为真，则启用详细日志记录。")
    need_confirm: bool = Field(default=False, description="如果为真，则工具使用需要确认。")

    def __init__(self, **kwargs: Any) -> None:
        """
        初始化配置实例，首先调用父类的初始化方法，然后读取本地配置文件来覆盖默认值。

        Args:
            **kwargs (Any): 传递给父类构造函数的任意关键字参数。
        """
        super().__init__(**kwargs)  # 调用 Pydantic 的默认初始化

        # 读取本地配置文件以覆盖默认值
        parser = configparser.ConfigParser()  # 创建配置解析器实例

        paths = self.path  # 获取配置文件路径列表
        if paths:  # 确保路径列表不为空
            try:
                config_files_read = parser.read(paths)  # 读取配置文件
            except configparser.Error as e:
                print(f"Warning: Error reading config file: {e}")  # 打印配置文件读取错误警告
                config_files_read = None

            if config_files_read:  # 如果成功读取了配置文件
                # 在 configparser 中，DEFAULT 是一个特殊的部分，不会出现在 sections() 的结果中
                # 我们可以直接使用 parser[CONFIG_SECTION] 来获取 DEFAULT 部分的内容
                section = parser[CONFIG_SECTION]  # 获取DEFAULT节的配置
                for field_name, field_info in self.__class__.model_fields.items():  # 遍历所有配置字段
                    if field_name in section:  # 如果配置文件中存在该字段
                        value_str = section[field_name]  # 获取配置值的字符串表示
                        try:
                            target_type = field_info.annotation  # 获取字段的目标类型
                            if target_type is int:  # 如果是整数类型
                                value: Any = int(value_str)  # 转换为整数
                            elif target_type is bool:  # 如果是布尔类型
                                # configparser.getboolean 处理 'yes'/'no', 'on'/'off', 'true'/'false', '1'/'0'
                                value = parser.getboolean(CONFIG_SECTION, field_name)  # 转换为布尔值
                            elif target_type == dict[str, Any]:  # 如果是字典类型
                                value = json.loads(value_str)  # 解析JSON字符串为字典
                            else:  # 默认为 str 类型
                                value = value_str  # 保持字符串格式
                            setattr(self, field_name, value)  # 设置配置值到实例属性
                        except (ValueError, json.JSONDecodeError) as e:
                            # 处理值转换或JSON解析错误
                            print(f"Warning: Could not parse config value for '{field_name}': {value_str}. Error: {e}")
                        except Exception as e:
                            # 处理其他异常
                            print(f"Warning: Error processing config for '{field_name}'. Error: {e}")

    @property
    def path(self) -> list[Path]:
        """
        获取配置文件路径列表，按照优先级顺序返回存在的配置文件路径。

        Returns:
            list[Path]: 配置文件路径列表，按优先级从高到低排序。
        """
        # 尝试从多个位置读取配置文件，例如当前目录或用户主目录
        config_path_local = Path(CONFIG_FILENAME)  # 当前目录下的配置文件路径
        config_path_home = Path(
            Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / CONFIG_APP_DIR / CONFIG_FILENAME
        )  # 用户主目录下的配置文件路径

        paths = []  # 初始化路径列表
        if config_path_local.exists():  # 如果当前目录下的配置文件存在
            paths.append(config_path_local)  # 添加到路径列表
        if config_path_home.exists():  # 如果用户主目录下的配置文件存在
            paths.append(config_path_home)  # 添加到路径列表
        return paths  # 返回路径列表


# 创建全局配置实例
config = Config()
