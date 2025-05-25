from typing import Self

from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy import exists
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import ChatCreate
from .schemas import ChatUpdateData
from src.database import Chat
from src.database import get_session


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_chat(self, chat_id: str, user_id: str | None = None) -> Chat | None:
        query = select(Chat).where(Chat.id == chat_id)
        if user_id:
            query = query.where(Chat.user_id == user_id)
        agent = (await self.session.execute(query)).scalar_one_or_none()
        return agent

    @staticmethod
    async def get_chats(user_id: str) -> Select:
        query = select(Chat).where(Chat.user_id == user_id).order_by(Chat.created_at.desc())
        return query

    async def update_chat(self, chat_id: str, data: ChatUpdateData) -> Chat:
        update_data: dict = data.model_dump(exclude_none=True)
        chat = await self.get_chat(chat_id=chat_id)
        assert chat, "Missing existence check"
        for k, v in update_data.items():
            setattr(chat, k, v)
        await self.session.flush()
        await self.session.refresh(chat)
        return chat

    async def create_chat(self, creation_data: ChatCreate) -> Chat:
        chat = Chat(
            **creation_data.chat_data.model_dump(exclude_none=True),
            user_id=creation_data.current_user_id,
        )
        self.session.add(chat)
        await self.session.flush()
        await self.session.refresh(chat)
        return chat

    async def delete_chat(self, chat_id: str) -> None:
        query = delete(Chat).where(Chat.id == chat_id)
        await self.session.execute(query)
        await self.session.flush()

    async def chat_exists(
        self, chat_id: str | None = None, agent_id: str | None = None, user_id: str | None = None
    ) -> bool:
        assert chat_id or agent_id or user_id, "Invalid params"
        exists_query = exists("*").select_from(Chat)
        if chat_id:
            exists_query = exists_query.where(Chat.id == chat_id)
        if agent_id:
            exists_query = exists_query.where(Chat.agent_id == agent_id)
        if user_id:
            exists_query = exists_query.where(Chat.user_id == user_id)
        query = select(exists_query)
        return await self.session.scalar(query)

    @classmethod
    def get_new_instance(cls, session: AsyncSession = Depends(get_session)) -> Self:
        return cls(session)
