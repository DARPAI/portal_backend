import json
from json import JSONDecodeError

from mcp import ClientSession
from mcp.client.sse import sse_client
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolParam

from src.agents.types import ToolInfo
from src.database import DARPServer
from src.errors import RemoteServerError
from src.messages.schemas import ToolCallData
from src.messages.schemas import ToolCallResult


class ToolManager:
    def __init__(self, darp_servers: list[DARPServer]) -> None:
        self.renamed_tools: dict[str, ToolInfo] = {}
        self.tools: list[ChatCompletionToolParam] = []
        self.darp_servers = darp_servers
        self.set_tools()

    def rename_and_save(self, tool_name: str, server: DARPServer) -> str:
        renamed_tool = f"{tool_name}_darp_{server.name}"
        self.renamed_tools[renamed_tool] = ToolInfo(tool_name=tool_name, server=server)
        return renamed_tool

    def set_tools(self) -> None:
        tools = []
        for server in self.darp_servers:
            for tool in server.tools:
                tool_name = self.rename_and_save(tool["name"], server=server)
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

    async def handle_tool_call(self, tool_call: ChatCompletionMessageToolCall) -> ToolCallResult:
        tool_info = self.renamed_tools.get(tool_call.function.name)
        if not tool_info:
            return ToolCallResult(
                server_id=None, tool_name=tool_call.function.name, result="Error: Incorrect tool name", success=False
            )
        server = tool_info.server
        async with sse_client(server.url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    tool_info.tool_name,
                    arguments=json.loads(tool_call.function.arguments) if tool_call.function.arguments else None,
                )
                try:
                    tool_result = json.loads(result.content[0].text)
                except JSONDecodeError:
                    tool_result = result.content[0].text
                return ToolCallResult(
                    server_id=int(server.id),
                    tool_name=tool_info.tool_name,
                    result=tool_result or "Error",
                    success=not result.isError,
                )

    def format_tool_call(self, tool_call: ChatCompletionMessageToolCall) -> ToolCallData:
        tool_info = self.renamed_tools.get(tool_call.function.name)
        if not tool_info:
            raise RemoteServerError("Incorrect tool call from LLM")
        server_id = int(tool_info.server.id) if tool_info else None
        avatar = tool_info.server.logo if tool_info else None
        arguments = tool_call.function.arguments
        return ToolCallData(
            server_id=server_id,
            server_logo=avatar,
            tool_name=tool_info.tool_name,
            arguments=json.loads(arguments) if arguments else None,
        )
