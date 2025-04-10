from __future__ import annotations

import configparser
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Config(BaseModel):
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


config = Config()

# 读取本地配置文件以覆盖默认值
CONFIG_FILENAME = "config.ini"
CONFIG_APP_DIR = "uglychain"
CONFIG_SECTION = "uglychain"

parser = configparser.ConfigParser()
# 尝试从多个位置读取配置文件，例如当前目录或用户主目录
config_path_local = Path(CONFIG_FILENAME)
config_path_home = Path(Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / CONFIG_APP_DIR / CONFIG_FILENAME)
config_files_read = parser.read([config_path_local, config_path_home])

if config_files_read and parser.has_section(CONFIG_SECTION):
    section = parser[CONFIG_SECTION]
    for field_name, field_info in Config.model_fields.items():
        if field_name in section:
            value_str = section[field_name]
            try:
                target_type = field_info.annotation
                if target_type is int:
                    value: Any = int(value_str)
                elif target_type is bool:
                    # configparser.getboolean 处理 'yes'/'no', 'on'/'off', 'true'/'false', '1'/'0'
                    value = parser.getboolean(CONFIG_SECTION, field_name)
                elif target_type == dict[str, Any]:
                    value = json.loads(value_str)
                else:  # 默认为 str
                    value = value_str
                setattr(config, field_name, value)
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Warning: Could not parse config value for '{field_name}': {value_str}. Error: {e}")
            except Exception as e:
                print(f"Warning: Error processing config for '{field_name}'. Error: {e}")
