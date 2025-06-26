from datetime import datetime
from typing import Any
from typing import Literal
from typing import TypeAlias
from typing import Union

from pydantic import ConfigDict
from pydantic import RootModel

from ..chats.types import RoutingMode
from .types import DeepResearchLogEvent
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
    routing_mode: RoutingMode = RoutingMode.auto


class ToolCallResult(BaseSchema):
    server_id: int | None
    tool_call_id: str
    tool_name: str
    result: dict | list | str | bool | None
    success: bool


class ToolCallData(BaseSchema):
    tool_call_id: str
    server_logo: str | None
    server_id: int | None
    tool_name: str
    arguments: dict | None


class DeepResearchStageStart(BaseSchema):
    title: str


class DeepResearchStageFinish(BaseSchema):
    title: str
    summary: str
    full_text: str
    status: Literal["OK", "Error"]


class DeepResearchLogData(BaseSchema):
    event_type: DeepResearchLogEvent
    data: DeepResearchStageStart | DeepResearchStageFinish
    origin: Literal["darp/deepresearch"]


class GenericLogData(BaseSchema):
    data: Any


class ErrorData(BaseSchema):
    status_code: int
    detail: dict


EventData: TypeAlias = Union[
    TextChunkData, MessageRead, ToolCallData, ToolCallResult, DeepResearchLogData, GenericLogData, ErrorData
]


class Event(BaseSchema):
    event_type: EventType
    data: EventData


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


class ToolMessageForLLM(BaseSchema):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    role: Literal["tool"]
    content: str
    tool_call_id: str
