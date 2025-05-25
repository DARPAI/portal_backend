from datetime import datetime

from pydantic import field_validator

from src.base_schema import BaseSchema


class DARPServerRead(BaseSchema):
    id: str
    name: str
    description: str | None = None
    logo: str | None
    updated_at: datetime


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
    logo: str | None
    tools: list[dict]

    @field_validator("id", mode="before")  # noqa
    @classmethod
    def validate_a(cls, value: int) -> str:
        return str(value)
