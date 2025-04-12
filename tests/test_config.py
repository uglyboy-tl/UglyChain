from __future__ import annotations

import configparser
from pathlib import Path
from unittest.mock import patch

import pytest

from uglychain.config import CONFIG_APP_DIR, CONFIG_FILENAME, Config


def mock_config_path(monkeypatch, config_paths: list[Path]) -> None:
    """设置 Config.path 属性返回指定的配置文件路径"""

    def mock_path(_self) -> list[Path]:
        return config_paths

    monkeypatch.setattr(Config, "path", property(mock_path))


@pytest.fixture
def config_file(tmp_path):
    """创建一个临时配置文件用于测试"""
    config_content = """
[DEFAULT]
default_model = test_model
default_api_params = {"temperature": 0.7}
default_language = English
response_markdown_type = json
llm_max_retry = 5
llm_timeout = 60
llm_wait_time = 2
use_parallel_processing = true
session_log = false
verbose = true
need_confirm = true
"""
    config_path = tmp_path / CONFIG_FILENAME
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def invalid_config_file(tmp_path):
    """创建一个包含无效值的配置文件用于测试"""
    config_content = """
[DEFAULT]
default_model = test_model
default_api_params = {invalid_json}
llm_max_retry = not_an_integer
use_parallel_processing = not_a_boolean
"""
    config_path = tmp_path / CONFIG_FILENAME
    config_path.write_text(config_content)
    return config_path


def test_config_default_values():
    """测试配置的默认值"""
    # 使用patch来确保不读取任何配置文件
    with patch("pathlib.Path.exists", return_value=False):
        config = Config()
        assert config.default_model == "openai:gpt-4o-mini"
        assert config.default_api_params == {}
        assert config.default_language == "Chinese"
        assert config.response_markdown_type == "yaml"
        assert config.llm_max_retry == 3
        assert config.llm_timeout == 30
        assert config.llm_wait_time == 0
        assert config.use_parallel_processing is False
        assert config.session_log is True
        assert config.verbose is False
        assert config.need_confirm is False


def test_config_from_file(config_file, monkeypatch):
    """测试从配置文件加载配置"""
    # 使用辅助函数设置配置文件路径
    mock_config_path(monkeypatch, [config_file])

    # 创建配置对象
    config = Config()

    # 验证配置值
    assert config.default_model == "test_model"
    assert config.default_api_params == {"temperature": 0.7}
    assert config.default_language == "English"
    assert config.response_markdown_type == "json"
    assert config.llm_max_retry == 5
    assert config.llm_timeout == 60
    assert config.llm_wait_time == 2
    assert config.use_parallel_processing is True
    assert config.session_log is False
    assert config.verbose is True
    assert config.need_confirm is True


def test_config_from_home_directory(tmp_path, monkeypatch):
    """测试从用户主目录加载配置"""
    # 创建配置文件在模拟的主目录
    config_dir = tmp_path / ".config" / CONFIG_APP_DIR
    config_dir.mkdir(parents=True)
    config_path = config_dir / CONFIG_FILENAME

    config_content = """
[DEFAULT]
default_model = home_model
default_language = Spanish
"""
    config_path.write_text(config_content)

    # 使用辅助函数设置配置文件路径
    mock_config_path(monkeypatch, [config_path])

    # 创建配置对象
    config = Config()

    # 验证配置值
    assert config.default_model == "home_model"
    assert config.default_language == "Spanish"


def test_config_with_invalid_values(invalid_config_file, monkeypatch, capsys):
    """测试处理无效配置值"""
    # 使用辅助函数设置配置文件路径
    mock_config_path(monkeypatch, [invalid_config_file])

    # 创建配置对象
    config = Config()

    # 检查默认值是否保持不变
    assert config.default_model == "test_model"  # 这个值是有效的
    assert config.default_api_params == {}  # 应该使用默认值，因为JSON无效
    assert config.llm_max_retry == 3  # 应该使用默认值，因为不是整数
    assert config.use_parallel_processing is False  # 应该使用默认值，因为不是布尔值

    # 检查是否打印了警告
    captured = capsys.readouterr()
    assert "Warning: Could not parse config value for 'default_api_params'" in captured.out
    assert "Warning: Could not parse config value for 'llm_max_retry'" in captured.out
    assert "Warning: Could not parse config value for 'use_parallel_processing'" in captured.out


def test_config_with_xdg_config_home(tmp_path, monkeypatch):
    """测试使用 XDG_CONFIG_HOME 环境变量"""
    # 创建配置文件在 XDG_CONFIG_HOME 目录
    xdg_config_dir = tmp_path / "xdg_config" / CONFIG_APP_DIR
    xdg_config_dir.mkdir(parents=True)
    config_path = xdg_config_dir / CONFIG_FILENAME

    config_content = """
[DEFAULT]
default_model = xdg_model
"""
    config_path.write_text(config_content)

    # 使用辅助函数设置配置文件路径
    mock_config_path(monkeypatch, [config_path])

    # 创建配置对象
    config = Config()

    # 验证配置值
    assert config.default_model == "xdg_model"


def test_config_with_other_section(tmp_path, monkeypatch):
    """测试配置文件中有其他部分但没有 DEFAULT 部分"""
    config_content = """
[OTHER_SECTION]
default_model = other_model
"""
    config_path = tmp_path / CONFIG_FILENAME
    config_path.write_text(config_content)

    # 使用辅助函数设置配置文件路径
    mock_config_path(monkeypatch, [config_path])

    # 创建配置对象
    config = Config()

    # 验证配置值
    # 应该使用默认值，因为没有 DEFAULT 部分
    assert config.default_model == "openai:gpt-4o-mini"


def test_config_with_unexpected_exception(tmp_path, monkeypatch):
    """测试处理意外异常"""
    # 创建一个有效的配置文件
    config_content = """
[DEFAULT]
default_model = test_model
"""
    config_path = tmp_path / CONFIG_FILENAME
    config_path.write_text(config_content)

    # 使用辅助函数设置配置文件路径
    mock_config_path(monkeypatch, [config_path])

    # 模拟 configparser.ConfigParser.__getitem__ 方法抛出异常
    def mock_getitem(_self, _section):
        raise Exception("Unexpected error")

    # 使用monkeypatch来覆盖__getitem__方法
    monkeypatch.setattr(configparser.ConfigParser, "__getitem__", mock_getitem)

    # 验证异常被抛出
    with pytest.raises(Exception, match="Unexpected error"):
        Config()


def test_config_with_custom_values(monkeypatch):
    """测试使用自定义值初始化配置"""
    custom_values = {"default_model": "custom_model", "default_language": "French", "llm_max_retry": 10}

    # 使用辅助函数设置空的配置文件路径
    mock_config_path(monkeypatch, [])

    # 创建配置对象，使用自定义值
    config = Config(**custom_values)

    # 验证配置值
    assert config.default_model == "custom_model"
    assert config.default_language == "French"
    assert config.llm_max_retry == 10
    # 其他值应该是默认值
    assert config.default_api_params == {}
    assert config.response_markdown_type == "yaml"
