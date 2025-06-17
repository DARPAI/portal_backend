from datetime import datetime
from typing import Any

from pydantic import field_serializer
from pydantic import field_validator

from src.base_schema import BaseSchema


class ToolSchema(BaseSchema):
    name: str
    alias: str
    description: str
    input_schema: dict[str, Any]


class DARPServerRead(BaseSchema):
    id: str
    name: str
    description: str | None = None
    logo: str | None = None
    transport_protocol: str
    updated_at: datetime

    @field_serializer("id")
    def serialize_id(self, id: str, _info) -> int:  # noqa
        return int(id)


class DARPServerWithTools(DARPServerRead):
    tools: list[dict]


class DARPServerCreate(BaseSchema):
    name: str
    description: str | None = None
    url: str
    tools: list[dict]


class RegistryServerSchema(BaseSchema):
    id: str
    name: str
    description: str
    url: str
    logo: str | None = None
    transport_protocol: str
    tools: list[ToolSchema]

    @field_validator("id", mode="before")  # noqa
    @classmethod
    def validate_a(cls, value: int) -> str:
        return str(value)

    @field_serializer("tools")
    def serialize_tools(self, tools: list[ToolSchema], _info) -> list[dict]:
        return [tool.model_dump() for tool in tools]
