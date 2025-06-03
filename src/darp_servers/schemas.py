from datetime import datetime

from pydantic import field_serializer
from pydantic import field_validator

from src.base_schema import BaseSchema


class DARPServerRead(BaseSchema):
    id: str
    name: str
    description: str | None = None
    logo: str | None = None
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
    tools: list[dict]

    @field_validator("id", mode="before")  # noqa
    @classmethod
    def validate_a(cls, value: int) -> str:
        return str(value)
