from __future__ import annotations

from uglychain import config, react
from uglychain.tools.browser_use import BrowserUse

config.verbose = True


@react(tools=[BrowserUse])
def ask():
    return "帮我在豆瓣上搜索一下仙剑1的女主角，看看她最近还有什么作品？"


ask()
