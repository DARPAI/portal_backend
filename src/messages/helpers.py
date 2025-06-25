from collections.abc import AsyncGenerator
from typing import Any

from .types import EventType
from src.errors import FastApiError
from src.messages.schemas import ErrorData
from src.messages.schemas import Event


async def convert_stream_errors(stream: AsyncGenerator[str, Any]) -> AsyncGenerator[str, Any]:
    try:
        async for chunk in stream:
            yield chunk
    except FastApiError as error:
        data = ErrorData(status_code=error.status_code, detail=error.detail)
        yield Event(event_type=EventType.error, data=data).model_dump_json()
