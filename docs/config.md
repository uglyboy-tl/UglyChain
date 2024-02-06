# 配置

## 配置方法

程序的运行需要读取环境变量来获取配置信息，因此需要在运行程序之前设置环境变量。
例如配置默认的 LLM 为 `gpt-3.5-turbo`，可以使用以下命令设置环境变量。

```bash
export LLM_PROVIDER=gpt-3.5-turbo
```

若需要永久设置环境变量，可以将上述命令添加到 `~/.bashrc` 或 `~/.zshrc` 文件中。

更为推荐的方法是，在项目根目录下创建 `.env` 文件，然后在文件中添加配置项。
VSCode 的用户会自动根据 `.env` 文件中的配置项获得环境变量。

如果需要在程序中获取 `.env` 文件中的配置项，可以使用 `python-dotenv` 库。

```python
from dotenv import load_dotenv
load_dotenv()
```

## 配置项

```.env
LLM_PROVIDER # 默认的 LLM 提供商

# OpenAI 的 API 配置
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=

# Copilot4GPT 的 API 配置
COPILOT_TOKEN=ghu_xxx
COPILOT_GPT4_SERVICE_URL=

# YI 的 API 配置
YI_API_KEY=xxx

# 通义千问 的 API 配置
DASHSCOPE_API_KEY=sk-xxx

# 智谱 ChatGLM 的 API 配置
ZHIPUAI_API_KEY=xxx

# GEMINI 的 API 配置
GEMINI_API_KEY=xxx

# 百川大模型 的 API 配置
BAICHUAN_API_KEY=sk-xxx

# Bing 的 API 配置
BING_SUBSCRIPTION_KEY=xxx
```
