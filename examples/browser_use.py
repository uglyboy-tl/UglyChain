from __future__ import annotations

from uglychain import config, react
from uglychain.tools.browser_use import BrowserUse

config.verbose = True
config.default_model = "openrouter:deepseek/deepseek-chat"


@react(tools=[BrowserUse])
def ask():
    return (
        "用浏览器搜索豆瓣网，通过链接进入豆瓣，再通过豆瓣电影查一下仙剑1女主角的演员是谁，然后看看她最近还有什么作品？"
    )


ask()
