from typing import Self

from fastapi import Depends
from sqlalchemy import Select

from .repository import ChatRepository
from .schemas import ChatCreate
from .schemas import ChatUpdate
from src.agents.repository import AgentRepository
from src.database import Chat
from src.errors import InvalidData
from src.errors import NotFoundError


class ChatService:
    def __init__(self, repo: ChatRepository, agent_repo: AgentRepository) -> None:
        self.repo = repo
        self.agent_repo = agent_repo

    async def get_single_chat(self, chat_id: str, current_user_id: str) -> Chat:
        chat = await self.repo.get_chat(chat_id=chat_id, user_id=current_user_id)
        if not chat:
            raise NotFoundError(message="Chat with this id does not exist")
        return chat

    async def get_chats(self, user_id: str) -> Select:
        return await self.repo.get_chats(user_id=user_id)

    async def update_chat(self, chat_id: str, data: ChatUpdate) -> Chat:
        if not await self.repo.chat_exists(chat_id=chat_id, user_id=data.current_user_id):
            raise NotFoundError(message="Chat with this id does not exist")
        chat = await self.repo.update_chat(chat_id=chat_id, data=data.update_data)
        return chat

    async def create_chat(self, creation_data: ChatCreate) -> Chat:
        agent_exists = await self.agent_repo.agent_exists(
            agent_id=creation_data.chat_data.agent_id, user_id=creation_data.current_user_id
        )
        if not agent_exists:
            raise InvalidData("Invalid agent_id")
        return await self.repo.create_chat(creation_data)

    async def delete_chat(self, chat_id: str, current_user_id: str) -> None:
        chat = await self.repo.chat_exists(chat_id=chat_id, user_id=current_user_id)
        if not chat:
            raise NotFoundError(message="Chat with this id does not exist")
        await self.repo.delete_chat(chat_id=chat_id)

    @classmethod
    def get_new_instance(
        cls,
        repo: ChatRepository = Depends(ChatRepository.get_new_instance),
        agent_repo: AgentRepository = Depends(AgentRepository.get_new_instance),
    ) -> Self:
        return cls(repo=repo, agent_repo=agent_repo)
