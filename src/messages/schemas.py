from datetime import datetime
from typing import Literal

from pydantic import ConfigDict
from pydantic import RootModel

from .types import EventType
from .types import MessageSource
from src.base_schema import BaseSchema
from src.llm_clients.types import TextChunkData


class MessageRead(BaseSchema):
    id: str
    user_id: str
    chat_id: str
    agent_id: str
    model: str
    source: MessageSource
    content: list[dict]
    created_at: datetime


class MessageCreateData(BaseSchema):
    text: str | None


class MessageCreate(BaseSchema):
    current_user_id: str
    data: MessageCreateData
    routing: bool = False


class ToolCallResult(BaseSchema):
    server_id: int | None
    tool_name: str
    result: dict | list | str | bool | None
    success: bool


class ToolCallData(BaseSchema):
    tool_call_id: str
    server_logo: str | None
    server_id: int | None
    tool_name: str
    arguments: dict | None


class Event(BaseSchema):
    event_type: EventType
    data: TextChunkData | MessageRead | ToolCallData | ToolCallResult


class LLMToolCall(BaseSchema):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    function: dict
    type: Literal["function"]


LLMToolCalls = RootModel[list[LLMToolCall]]


class AssistantMessage(BaseSchema):
    role: Literal["assistant"]
    content: str | None
    tool_calls: LLMToolCalls | None  # type: ignore
