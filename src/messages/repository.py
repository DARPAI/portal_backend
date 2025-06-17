import json
from typing import Literal
from typing import Self

from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy import exists
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import DeepResearchLogData
from .schemas import GenericLogData
from .schemas import MessageCreate
from .schemas import ToolCallData
from .types import MessageSource
from src.database import Agent
from src.database import get_session
from src.database import Message


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_message(self, message_id: str, user_id: str | None = None) -> Message | None:
        query = select(Message).where(Message.id == message_id)
        if user_id:
            query = query.where(Message.user_id == user_id)
        agent = (await self.session.execute(query)).scalar_one_or_none()
        return agent

    @staticmethod
    async def get_messages(chat_id: str, order: Literal["asc", "desc"] = "desc") -> Select:
        query = select(Message).where(Message.chat_id == chat_id)
        if order == "desc":
            query = query.order_by(Message.created_at.desc())
        else:
            query = query.order_by(Message.created_at.asc())
        return query

    async def create_user_message(self, chat_id: str, creation_data: MessageCreate, agent: Agent) -> Message:
        message = Message(
            chat_id=chat_id,
            agent_id=agent.id,
            model=agent.model,
            source=MessageSource.user,
            content=[self.format_text_message(text_message=creation_data.data.text)],
            user_id=creation_data.current_user_id,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def create_llm_message(
        self,
        chat_id: str,
        agent: Agent,
        tool_calls: list[ToolCallData],
        creation_data: MessageCreate,
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            agent_id=agent.id,
            model=agent.model,
            source=MessageSource.llm,
            content=[self.format_llm_message(text=creation_data.data.text, tool_calls=tool_calls)],
            user_id=creation_data.current_user_id,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def create_tool_message(
        self,
        chat_id: str,
        agent: Agent,
        tool_call_id: str,
        tool_call_result: str,
        current_user_id: str,
        tool_call_logs: list[DeepResearchLogData | GenericLogData],
    ) -> Message:
        message_content = [
            self.format_tool_message(
                tool_call_id=tool_call_id, tool_call_result=tool_call_result, tool_call_logs=tool_call_logs
            )
        ]
        message = Message(
            chat_id=chat_id,
            agent_id=agent.id,
            model=agent.model,
            source=MessageSource.tool,
            content=message_content,
            user_id=current_user_id,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    @staticmethod
    def format_tool_message(
        tool_call_id: str, tool_call_result: str, tool_call_logs: list[DeepResearchLogData | GenericLogData]
    ) -> dict:
        return dict(
            tool_call_id=tool_call_id,
            content=tool_call_result,
            role="tool",
            tool_call_logs=[log.model_dump() for log in tool_call_logs],
        )

    async def delete_message(self, message_id: str) -> None:
        query = delete(Message).where(Message.id == message_id)
        await self.session.execute(query)
        await self.session.flush()

    async def message_exists(
        self, message_id: str | None = None, chat_id: str | None = None, user_id: str | None = None
    ) -> bool:
        assert message_id or chat_id or user_id, "Invalid params"
        exists_query = exists("*").select_from(Message)
        if message_id:
            exists_query = exists_query.where(Message.id == message_id)
        if chat_id:
            exists_query = exists_query.where(Message.chat_id == chat_id)
        if user_id:
            exists_query = exists_query.where(Message.user_id == user_id)
        query = select(exists_query)
        return await self.session.scalar(query)

    @staticmethod
    def format_text_message(text_message: str | None) -> dict:
        return dict(content=text_message, role="user")

    @staticmethod
    def format_llm_message(text: str | None, tool_calls: list[ToolCallData]) -> dict:
        llm_tool_calls = [
            {
                "id": tool_call.tool_call_id,
                "function": {
                    "arguments": json.dumps(tool_call.arguments) if tool_call.arguments else "{}",
                    "name": tool_call.tool_name,
                },
                "type": "function",
                "server_id": tool_call.server_id,
                "server_logo": tool_call.server_logo,
            }
            for tool_call in tool_calls
        ]
        return dict(role="assistant", content=text, tool_calls=llm_tool_calls if len(llm_tool_calls) > 0 else None)

    @classmethod
    def get_new_instance(
        cls,
        session: AsyncSession = Depends(get_session),
    ) -> Self:
        return cls(session)
