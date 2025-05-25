from enum import StrEnum


class MessageSource(StrEnum):
    user = "user"
    llm = "llm"
    tool = "tool"


class EventType(StrEnum):
    message_creation = "message_creation"
    text_chunk = "text_chunk"
    tool_call = "tool_call"
    tool_call_result = "tool_call_result"
