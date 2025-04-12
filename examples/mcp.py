from __future__ import annotations

import os

from uglychain import Tool, config, react


@Tool.mcp
class amap_mcp_server:
    command = "npx"
    args = ["-y", "@amap/amap-maps-mcp-server"]
    env = {"AMAP_MAPS_API_KEY": ""}


@Tool.mcp
class amap_mcp_sse:
    command = f"https://mcp.amap.com/sse?key={os.getenv('AMAP_MAPS_API_KEY')}"


@Tool.mcp
class thinking_mcp_server:
    command = "npx"
    args = ["-y", "@zengwenliang/mcp-server-sequential-thinking"]


@Tool.mcp
class firecrawl_mcp:
    command = "npx"
    args = ["-y", "firecrawl-mcp"]


if __name__ == "__main__":
    config.verbose = True

    @react("deepseek:deepseek-chat", tools=[amap_mcp_server, thinking_mcp_server])
    def main(prompt: str):
        return prompt

    # main("帮我看看北京东城区和平里中街3号院附近有什么好吃的")
    main("今天北京的天气怎么样？")
