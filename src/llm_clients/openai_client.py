from collections.abc import AsyncGenerator
from typing import Any

from httpx import AsyncClient
from httpx import URL
from openai import APIError
from openai import AsyncOpenAI
from openai import AsyncStream
from openai import InternalServerError
from openai import NOT_GIVEN
from openai import OpenAIError
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionChunk
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat import ChatCompletionToolChoiceOptionParam
from openai.types.chat import ChatCompletionToolParam
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.chat.chat_completion_message_tool_call import Function

from .types import TextChunkData
from src.errors import RemoteServerError
from src.logger import logger
from src.settings import settings

default_http_client: AsyncClient = AsyncClient() if settings.PROXY is None else AsyncClient(proxy=settings.PROXY)


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        http_client: AsyncClient = default_http_client,
        base_url: str | URL | None = None,
    ) -> None:
        self.llm_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client,
        )
        self.request_timeout = 20

    async def stream(
        self,
        model: str,
        conversation: list[ChatCompletionMessageParam],
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        tools: list[ChatCompletionToolParam] | None = None,
        tool_choice: ChatCompletionToolChoiceOptionParam = "auto",
    ) -> AsyncGenerator[list[ChatCompletionMessageToolCall] | TextChunkData, Any]:
        response = await self.get_response(
            conversation=conversation,
            max_tokens=max_tokens,
            stream=True,
            tools=tools,
            model=model,
            system_prompt=system_prompt,
            tool_choice=tool_choice,
        )
        assert isinstance(response, AsyncStream)
        return self.formatted_stream_generator(response)

    async def get_response(
        self,
        model: str,
        conversation: list[ChatCompletionMessageParam],
        tool_choice: ChatCompletionToolChoiceOptionParam,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        tools: list[ChatCompletionToolParam] | None = None,
    ) -> ChatCompletion | AsyncStream[ChatCompletionChunk]:
        system_message: list[dict] = []
        if system_prompt:
            # Anthropic prompt caching
            system_message = [{"role": "system", "content": system_prompt, "cache_control": {"type": "ephemeral"}}]
        final_conversation = system_message + conversation
        try:
            response = await self.llm_client.chat.completions.create(
                model=model,
                messages=final_conversation,
                max_tokens=max_tokens,
                stream=stream,
                tools=tools or NOT_GIVEN,
                tool_choice=tool_choice,
                timeout=self.request_timeout,
            )
        except APIError as e:
            logger.error(e.code)
            logger.error(e.body)
            raise RemoteServerError("LLM request failed")
        except InternalServerError as e:
            logger.error(e.response.json())
            raise RemoteServerError("LLM request failed")
        except OpenAIError as e:
            logger.error(f"Request to Provider failed with the following exception:\n{e}")
            raise RemoteServerError("LLM request failed")
        return response

    @staticmethod
    def get_empty_openai_tool_call() -> dict:
        return {"id": None, "function": {"arguments": "", "name": ""}, "type": "function"}

    @staticmethod
    def format_tool_calls(tool_calls: dict) -> list[ChatCompletionMessageToolCall]:
        return [
            ChatCompletionMessageToolCall(
                id=tool_calls[key]["id"],
                function=Function(
                    name=tool_calls[key]["function"]["name"], arguments=tool_calls[key]["function"]["arguments"]
                ),
                type="function",
            )
            for key in tool_calls
        ]

    async def formatted_stream_generator(
        self,
        stream: AsyncStream[ChatCompletionChunk],
    ) -> AsyncGenerator[list[ChatCompletionMessageToolCall] | TextChunkData, Any]:
        tool_calls: dict = {}
        async for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta
            logger.debug(delta)
            if choice.finish_reason == "tool_calls":
                formatted_tool_calls = self.format_tool_calls(tool_calls)
                yield formatted_tool_calls
                continue
            if delta.content:
                yield TextChunkData(content=delta.content)
            if delta.tool_calls:
                self._add_tool_call_piece(tool_calls=tool_calls, delta=delta)

    def _add_tool_call_piece(self, tool_calls: dict, delta: ChoiceDelta) -> None:
        piece = delta.tool_calls[0]
        tool_calls[piece.index] = tool_calls.get(piece.index, self.get_empty_openai_tool_call())
        if piece.id:
            tool_calls[piece.index]["id"] = piece.id
        if piece.function.name:
            tool_calls[piece.index]["function"]["name"] = piece.function.name
        if piece.function.arguments:
            tool_calls[piece.index]["function"]["arguments"] += piece.function.arguments
