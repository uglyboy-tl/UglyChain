from __future__ import annotations

from pydantic import BaseModel

from uglychain import config, react
from uglychain.default_tools import e2b_mcp_server, execute_command, visit_webpage, web_search
from uglychain.tools import Tool


class Date(BaseModel):
    year: int


@react("openai:gpt-4o-mini", [web_search], response_format=Date)
def search(name: str):
    return f"{name}生于哪一年？"


@react(tools=[execute_command])
def update(message_history: list[dict[str, str]]):
    return message_history


@react("openai:gpt-4o-mini", [execute_command, visit_webpage])
def weather(city: str):
    return f"使用 wttr.in 获取{city}的天气信息"


@react(tools=e2b_mcp_server.tools)
def code_interpreter(question: str):
    return f"{question}"


if __name__ == "__main__":
    config.verbose = True
    # config.need_confirm = True
    # search("牛顿")
    update([{"role": "user", "content": "更新我的电脑系统"}])
    # weather("北京")
    # code_interpreter("我买房贷款了187万，贷款的年利率是4.9%，贷款期限是30年，每月还款多少？")
