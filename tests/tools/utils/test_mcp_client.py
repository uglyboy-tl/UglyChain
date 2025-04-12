from __future__ import annotations

import asyncio

import pytest
from mcp import ClientSession, StdioServerParameters, types
from pydantic.networks import AnyUrl

from uglychain.tools.utils.mcp_client import McpClient, McpResource, McpTool


@pytest.fixture
def mock_session(mocker):
    """创建一个模拟的ClientSession对象"""
    session = mocker.MagicMock(spec=ClientSession)
    return session


@pytest.fixture
def mock_client(mocker, mock_session):
    """创建一个模拟的McpClient对象"""
    client = mocker.MagicMock(spec=McpClient)
    client._session = mock_session
    client.session = mock_session
    client._loop = asyncio.new_event_loop()
    return client


class TestMcpTool:
    @pytest.mark.asyncio
    async def test_arun_text_content(self, mock_client, mocker):
        """测试_arun方法处理TextContent类型的响应"""
        # 准备
        tool = McpTool("test_client", mock_client, "test_tool", "Test tool description")
        text_content = types.TextContent(type="text", text="Test result")
        result = mocker.MagicMock()
        result.content = [text_content]
        # 直接设置返回值，不使用Future
        mock_client.session.call_tool.return_value = result

        # 执行
        response = await tool._arun(param="test")

        # 验证
        mock_client.session.call_tool.assert_called_once_with("test_tool", arguments={"param": "test"})
        assert response == "Test result"

    @pytest.mark.asyncio
    async def test_arun_image_content(self, mock_client, mocker):
        """测试_arun方法处理ImageContent类型的响应"""
        # 准备
        tool = McpTool("test_client", mock_client, "test_tool")
        image_content = types.ImageContent(type="image", data="image_data", mimeType="image/png")
        result = mocker.MagicMock()
        result.content = [image_content]
        # 直接设置返回值，不使用Future
        mock_client.session.call_tool.return_value = result

        # 执行
        response = await tool._arun()

        # 验证
        assert response == "image_data"

    @pytest.mark.asyncio
    async def test_arun_embedded_text_resource(self, mock_client, mocker):
        """测试_arun方法处理EmbeddedResource类型的响应"""
        # 准备
        tool = McpTool("test_client", mock_client, "test_tool")
        text_resource = types.TextResourceContents(uri=AnyUrl("resource://embedded"), text="Embedded text")
        embedded_resource = types.EmbeddedResource(type="resource", resource=text_resource)
        result = mocker.MagicMock()
        result.content = [embedded_resource]
        # 直接设置返回值，不使用Future
        mock_client.session.call_tool.return_value = result

        # 执行
        response = await tool._arun()

        # 验证
        assert response == "Embedded text"

    @pytest.mark.asyncio
    async def test_arun_unsupported_content(self, mock_client, mocker):
        """测试_arun方法处理不支持的内容类型"""
        # 准备
        tool = McpTool("test_client", mock_client, "test_tool")
        unsupported_content = mocker.MagicMock()  # 创建一个不支持的内容类型
        result = mocker.MagicMock()
        result.content = [unsupported_content]
        # 直接设置返回值，不使用Future
        mock_client.session.call_tool.return_value = result

        # 执行和验证
        with pytest.raises(ValueError, match="Unsupported content type:"):
            await tool._arun()

    def test_call(self, mock_client):
        """测试__call__方法"""
        # 准备
        tool = McpTool("test_client", mock_client, "test_tool")
        mock_client._executor.submit.return_value.result.return_value = "Test result"

        # 执行
        result = tool(param="test")

        # 验证
        assert result == "Test result"
        mock_client._executor.submit.assert_called_once()


class TestMcpResource:
    @pytest.mark.asyncio
    async def test_aread_text_resource(self, mock_client, mocker):
        """测试_aread方法处理TextResourceContents类型的响应"""
        # 准备
        resource = McpResource("test_client", mock_client, "test_resource", AnyUrl("resource://test"))
        text_content = types.TextResourceContents(uri=AnyUrl("resource://test"), text="Test resource content")
        response = mocker.MagicMock()
        response.contents = [text_content]
        # 直接设置返回值，不使用Future
        mock_client.session.read_resource.return_value = response

        # 执行
        result = await resource._aread()

        # 验证
        mock_client.session.read_resource.assert_called_once()
        assert mock_client.session.read_resource.call_args[0][0] == AnyUrl("resource://test")
        assert result == ["Test resource content"]

    @pytest.mark.asyncio
    async def test_aread_blob_resource(self, mock_client, mocker):
        """测试_aread方法处理BlobResourceContents类型的响应"""
        # 准备
        resource = McpResource("test_client", mock_client, "test_resource", AnyUrl("resource://test"))
        blob_content = types.BlobResourceContents(uri=AnyUrl("resource://test"), blob="blob_data")
        response = mocker.MagicMock()
        response.contents = [blob_content]
        # 直接设置返回值，不使用Future
        mock_client.session.read_resource.return_value = response

        # 执行
        result = await resource._aread()

        # 验证
        assert result == ["blob_data"]

    @pytest.mark.asyncio
    async def test_aread_unsupported_content(self, mock_client, mocker):
        """测试_aread方法处理不支持的内容类型"""
        # 准备
        resource = McpResource("test_client", mock_client, "test_resource", AnyUrl("resource://test"))
        unsupported_content = mocker.MagicMock()  # 创建一个不支持的内容类型
        response = mocker.MagicMock()
        response.contents = [unsupported_content]
        # 直接设置返回值，不使用Future
        mock_client.session.read_resource.return_value = response

        # 执行和验证
        with pytest.raises(ValueError, match="Unsupported content type:"):
            await resource._aread()

    @pytest.mark.asyncio
    async def test_aread_with_uri_param(self, mock_client, mocker):
        """测试_aread方法使用传入的URI参数"""
        # 准备
        resource = McpResource("test_client", mock_client, "test_resource", AnyUrl("resource://default"))
        text_content = types.TextResourceContents(uri=AnyUrl("resource://custom"), text="Test content")
        response = mocker.MagicMock()
        response.contents = [text_content]
        # 直接设置返回值，不使用Future
        mock_client.session.read_resource.return_value = response

        # 执行
        result = await resource._aread(AnyUrl("resource://custom"))

        # 验证
        mock_client.session.read_resource.assert_called_once()
        assert mock_client.session.read_resource.call_args[0][0] == AnyUrl("resource://custom")
        assert result == ["Test content"]

    @pytest.mark.asyncio
    async def test_aread_no_uri(self, mock_client):
        """测试_aread方法在没有URI的情况下"""
        # 准备
        resource = McpResource("test_client", mock_client, "test_resource", "")

        # 执行和验证
        with pytest.raises(ValueError, match="URI is not set"):
            await resource._aread()

    def test_call(self, mock_client):
        """测试__call__方法"""
        # 准备
        resource = McpResource("test_client", mock_client, "test_resource", AnyUrl("resource://test"))
        mock_client._executor.submit.return_value.result.return_value = ["Test content"]

        # 执行
        result = resource()

        # 验证
        assert result == ["Test content"]
        mock_client._executor.submit.assert_called_once()


class TestMcpClient:
    def test_create(self):
        """测试create静态方法"""
        client = McpClient.create("test", "command", ["arg1", "arg2"], {"ENV_VAR": "value"})
        assert client.name == "test"
        assert isinstance(client.server_param, StdioServerParameters)
        assert client.server_param.command == "command"
        assert client.server_param.args == ["arg1", "arg2"]
        assert client.server_param.env == {"ENV_VAR": "value"}

    def test_create_sse(self):
        """测试create_sse静态方法"""
        client = McpClient.create_sse("test", "http://example.com", {"Authorization": "Bearer token"}, 10, 300)
        assert client.name == "test"
        assert isinstance(client.server_param, dict)
        assert client.server_param["url"] == "http://example.com"
        assert client.server_param["headers"] == {"Authorization": "Bearer token"}
        assert client.server_param["timeout"] == 10
        assert client.server_param["sse_read_timeout"] == 300

    def test_create_websocket(self):
        """测试create_websocket静态方法"""
        client = McpClient.create_websocket("test", "ws://example.com")
        assert client.name == "test"
        assert client.server_param == "ws://example.com"

    @pytest.mark.asyncio
    async def test_start_session_stdio(self, mocker):
        """测试_start_session方法使用StdioServerParameters"""
        # 模拟stdio_client
        mock_stdio_client = mocker.patch("uglychain.tools.utils.mcp_client.stdio_client")
        mock_client = mocker.MagicMock()
        mock_read_write = (mocker.MagicMock(), mocker.MagicMock())

        # 创建一个真正的协程函数来替代__aenter__
        async def mock_aenter():
            return mock_read_write

        mock_client.__aenter__ = mock_aenter
        mock_stdio_client.return_value = mock_client

        # 模拟ClientSession
        mock_session = mocker.MagicMock(spec=ClientSession)
        mock_session_init = mocker.patch("uglychain.tools.utils.mcp_client.ClientSession", return_value=mock_session)

        # 创建一个真正的协程函数来替代__aenter__
        async def mock_session_aenter():
            return mock_session

        mock_session.__aenter__ = mock_session_aenter

        # 模拟initialize方法
        async def mock_initialize():
            return None

        mock_session.initialize = mock_initialize

        # 创建客户端
        client = McpClient("test", StdioServerParameters(command="cmd", args=[], env={}))
        # 设置exit_stack
        client.exit_stack = mocker.MagicMock()

        # 创建一个真正的协程函数来替代enter_async_context
        async def mock_enter_async_context(cm):
            if cm is mock_client:
                return mock_read_write
            return mock_session

        # 使用patch而不是直接赋值
        mocker.patch.object(client.exit_stack, "enter_async_context", mock_enter_async_context)

        # 执行
        await client._start_session()

        # 验证
        mock_stdio_client.assert_called_once()
        mock_session_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_sse(self, mocker):
        """测试_start_session方法使用SSE参数"""
        # 模拟sse_client
        mock_sse_client = mocker.patch("uglychain.tools.utils.mcp_client.sse_client")
        mock_client = mocker.MagicMock()
        mock_read_write = (mocker.MagicMock(), mocker.MagicMock())

        # 创建一个真正的协程函数来替代__aenter__
        async def mock_aenter():
            return mock_read_write

        mock_client.__aenter__ = mock_aenter
        mock_sse_client.return_value = mock_client

        # 模拟ClientSession
        mock_session = mocker.MagicMock(spec=ClientSession)
        mock_session_init = mocker.patch("uglychain.tools.utils.mcp_client.ClientSession", return_value=mock_session)

        # 创建一个真正的协程函数来替代__aenter__
        async def mock_session_aenter():
            return mock_session

        mock_session.__aenter__ = mock_session_aenter

        # 模拟initialize方法
        async def mock_initialize():
            return None

        mock_session.initialize = mock_initialize

        # 创建客户端
        client = McpClient("test", {"url": "http://example.com", "headers": {}, "timeout": 5, "sse_read_timeout": 300})

        # 设置exit_stack
        client.exit_stack = mocker.MagicMock()

        # 创建一个真正的协程函数来替代enter_async_context
        async def mock_enter_async_context(cm):
            if cm is mock_client:
                return mock_read_write
            return mock_session

        # 使用patch而不是直接赋值
        mocker.patch.object(client.exit_stack, "enter_async_context", mock_enter_async_context)

        # 执行
        await client._start_session()

        # 验证
        mock_sse_client.assert_called_once_with(url="http://example.com", headers={}, timeout=5, sse_read_timeout=300)
        mock_session_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_ainitialize(self, mocker):
        """测试_ainitialize方法"""
        # 准备
        client = McpClient("test", StdioServerParameters(command="cmd", args=[], env={}))

        # 模拟_start_session
        mock_session = mocker.MagicMock(spec=ClientSession)
        mocker.patch.object(client, "_start_session", return_value=mock_session)

        # 模拟工具列表
        tool1 = types.Tool(name="tool1", description="Tool 1", inputSchema={})
        tool2 = types.Tool(name="tool2", description="Tool 2", inputSchema={"param": {"type": "string"}})
        tools_result = types.ListToolsResult(tools=[tool1, tool2])
        # 直接设置返回值，不使用Future
        mock_session.list_tools.return_value = tools_result

        # 执行
        await client._ainitialize(True)

        # 验证
        mock_session.list_tools.assert_called_once()
        assert len(client._tools) == 2
        assert client._tools[0].name == "tool1"
        assert client._tools[1].name == "tool2"

    @pytest.mark.asyncio
    async def test_ainitialize_with_resources(self, mocker):
        """测试_ainitialize方法包含资源"""
        # 准备
        client = McpClient("test", StdioServerParameters(command="cmd", args=[], env={}), use_resources=True)

        # 模拟_start_session
        mock_session = mocker.MagicMock(spec=ClientSession)
        mocker.patch.object(client, "_start_session", return_value=mock_session)

        # 模拟工具列表
        tools_result = types.ListToolsResult(tools=[])
        # 直接设置返回值，不使用Future
        mock_session.list_tools.return_value = tools_result

        # 模拟资源列表
        resource1 = types.Resource(
            name="res1", uri=AnyUrl("resource://res1"), description="Resource 1", mimeType="text/plain"
        )
        resources_result = types.ListResourcesResult(resources=[resource1])
        # 直接设置返回值，不使用Future
        mock_session.list_resources.return_value = resources_result

        # 模拟资源模板列表
        template1 = types.ResourceTemplate(
            name="template1", uriTemplate="resource://template/{id}", description="Template 1", mimeType="text/plain"
        )
        templates_result = types.ListResourceTemplatesResult(resourceTemplates=[template1])
        # 直接设置返回值，不使用Future
        mock_session.list_resource_templates.return_value = templates_result

        # 执行
        await client._ainitialize(True)

        # 验证
        mock_session.list_resources.assert_called_once()
        mock_session.list_resource_templates.assert_called_once()
        assert len(client._resources) == 2
        assert client._resources[0].name == "res1"
        assert client._resources[1].name == "template1"

    @pytest.mark.asyncio
    async def test_close(self, mocker):
        """测试close方法"""
        # 准备
        client = McpClient("test", StdioServerParameters(command="cmd", args=[], env={}))
        mock_exit_stack = mocker.MagicMock()
        client.exit_stack = mock_exit_stack

        # 执行
        await client.close()

        # 验证
        mock_exit_stack.aclose.assert_called_once()
        assert client._session is None
        assert client._client is None
