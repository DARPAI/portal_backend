from datetime import datetime

from src.base_schema import BaseSchema


class ChatRead(BaseSchema):
    id: str
    title: str
    agent_id: str
    user_id: str
    created_at: datetime


class ChatData(BaseSchema):
    agent_id: str
    title: str | None = None


class ChatCreate(BaseSchema):
    chat_data: ChatData
    current_user_id: str


class ChatUpdateData(BaseSchema):
    title: str


class ChatUpdate(BaseSchema):
    update_data: ChatUpdateData
    current_user_id: str
