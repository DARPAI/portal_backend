import json
from asyncio import Queue
from contextlib import _AsyncGeneratorContextManager
from json import JSONDecodeError

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from src.agents.types import ToolInfo
from src.darp_servers.enums import DARPServerTransportProtocol
from src.darp_servers.log_collector import LogCollector
from src.database import DARPServer
from src.errors import RemoteServerError
from src.messages.schemas import DeepResearchLogData
from src.messages.schemas import GenericLogData
from src.messages.schemas import ToolCallData
from src.messages.schemas import ToolCallResult


class ToolManager:
    def __init__(
        self, darp_servers: list[DARPServer], queue: Queue[ToolCallResult | DeepResearchLogData | GenericLogData]
    ) -> None:
        self.renamed_tools: dict[str, ToolInfo] = {}
        self.original_to_renamed: dict[str, str] = {}
        self.tools: list[ChatCompletionToolParam] = []
        self.darp_servers = darp_servers
        self.set_tools()
        self.queue = queue

    def rename_and_save(self, tool_name: str, server: DARPServer, alias: str | None) -> str:
        alias = alias or f"{tool_name}__{server.name}"
        self.renamed_tools[alias] = ToolInfo(tool_name=tool_name, server=server)
        self.original_to_renamed[tool_name] = alias
        return alias

    def set_tools(self) -> None:
        tools = []
        for server in self.darp_servers:
            for tool in server.tools:
                tool_name = self.rename_and_save(tool_name=tool["name"], server=server, alias=tool.get("alias", None))
                tools.append(
                    ChatCompletionToolParam(
                        type="function",
                        function={
                            "name": tool_name,
                            "description": tool["description"],
                            "parameters": tool["input_schema"],
                        },
                    )
                )
        self.tools = tools

    async def handle_tool_call(self, tool_call: ChatCompletionMessageToolCall) -> None:
        tool_info = self.renamed_tools.get(tool_call.function.name)
        if not tool_info:
            await self.queue.put(
                ToolCallResult(
                    tool_call_id=tool_call.id,
                    server_id=None,
                    tool_name=tool_call.function.name,
                    result="Error: Incorrect tool name",
                    success=False,
                )
            )
            return
        server = tool_info.server
        client_ctx = self._get_client_context(server.url, server.transport_protocol)

        async with client_ctx as (read, write, *_):
            async with ClientSession(read, write, logging_callback=LogCollector(queue=self.queue)) as session:
                await session.initialize()

                result = await session.call_tool(
                    tool_info.tool_name,
                    arguments=json.loads(tool_call.function.arguments) if tool_call.function.arguments else None,
                )
                try:
                    tool_result = json.loads(result.content[0].text)
                except JSONDecodeError:
                    tool_result = result.content[0].text
                await self.queue.put(
                    ToolCallResult(
                        tool_call_id=tool_call.id,
                        server_id=int(server.id),
                        tool_name=tool_info.tool_name,
                        result=tool_result or "Error",
                        success=not result.isError,
                    )
                )

    def format_tool_call(self, tool_call: ChatCompletionMessageToolCall) -> ToolCallData:
        tool_info = self.renamed_tools.get(tool_call.function.name)
        if not tool_info:
            raise RemoteServerError("Incorrect tool call from LLM")
        server_id = int(tool_info.server.id) if tool_info else None
        avatar = tool_info.server.logo if tool_info else None
        arguments = tool_call.function.arguments
        return ToolCallData(
            tool_call_id=tool_call.id,
            server_id=server_id,
            server_logo=avatar,
            tool_name=tool_info.tool_name,
            arguments=json.loads(arguments) if arguments else None,
        )

    def rename_tool_calls(self, tool_calls: list[ToolCallData]) -> list[ToolCallData]:
        for tool_call in tool_calls:
            tool_call.tool_name = self.original_to_renamed[tool_call.tool_name]
        return tool_calls

    @classmethod
    def _get_client_context(
        cls,
        server_url: str,
        transport_protocol: DARPServerTransportProtocol,
    ) -> _AsyncGeneratorContextManager:
        if transport_protocol == DARPServerTransportProtocol.STREAMABLE_HTTP:
            client_ctx = streamablehttp_client(server_url)
        elif transport_protocol == DARPServerTransportProtocol.SSE:
            client_ctx = sse_client(server_url)
        else:
            raise RuntimeError("Unsupported transport protocol: %s", transport_protocol.name)

        return client_ctx
