from typing import Self

from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy import exists
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .constants import model_to_provider
from .schemas import AgentCreate
from .schemas import AgentUpdateData
from src.database import Agent
from src.database import agents_darp_servers
from src.database import Chat
from src.database import get_session


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_agent(self, agent_id: str, user_id: str | None = None) -> Agent | None:
        query = select(Agent).where(Agent.id == agent_id)
        if user_id:
            query = query.where(Agent.user_id == user_id)
        query = query.options(selectinload(Agent.darp_servers))
        agent = (await self.session.execute(query)).scalar_one_or_none()
        return agent

    async def get_agent_by_chat_id(self, chat_id: str) -> Agent:
        query = select(Agent).join(Chat).where(Agent.id == Chat.agent_id, Chat.id == chat_id)
        agent = (await self.session.execute(query)).scalar_one_or_none()
        assert agent, "Invalid db state"
        return agent

    @staticmethod
    async def get_agents(user_id: str | None) -> Select:
        query = select(Agent).order_by(Agent.created_at)
        if user_id:
            query = query.where(Agent.user_id == user_id)
        return query

    async def update_agent(
        self, agent_id: str, data: AgentUpdateData | None, server_ids: list[str] | None = None
    ) -> Agent:
        agent = await self.get_agent(agent_id=agent_id)
        assert agent, "Missing existence check"
        if server_ids is not None:
            await self.session.execute(delete(agents_darp_servers).where(agents_darp_servers.c.agent_id == agent_id))  # type: ignore
            await self.add_servers_to_agent(agent_id=agent_id, server_ids=server_ids)
        if not data:
            agent = await self.get_agent(agent_id=agent_id)
            await self.session.refresh(agent)
            return agent  # type: ignore
        update_data: dict = data.model_dump(exclude_none=True)
        if data.model:
            provider = model_to_provider.get(data.model)
            assert provider, "Invalid state of model and provider types"
            update_data["provider"] = provider
        for k, v in update_data.items():
            setattr(agent, k, v)
        await self.session.flush()
        await self.session.refresh(agent)
        return await self.get_agent(agent_id=agent_id)  # type: ignore

    async def create_agent(self, creation_data: AgentCreate, server_ids: list[str]) -> Agent:
        provider = model_to_provider.get(creation_data.agent_data.model)
        assert provider, "Invalid state of model and provider types"
        agent = Agent(
            **creation_data.agent_data.model_dump(exclude_none=True),
            user_id=creation_data.current_user_id,
            provider=provider,
        )
        self.session.add(agent)
        await self.session.flush()
        await self.session.refresh(agent)
        await self.add_servers_to_agent(agent_id=agent.id, server_ids=server_ids)
        agent_with_servers = await self.get_agent(agent_id=agent.id)
        assert agent_with_servers
        return agent_with_servers

    async def delete_agent(self, agent_id: str) -> None:
        query = delete(Agent).where(Agent.id == agent_id)
        await self.session.execute(query)

    async def add_servers_to_agent(self, agent_id, server_ids: list[str]) -> None:
        if server_ids:
            await self.session.execute(
                agents_darp_servers.insert(), [dict(agent_id=agent_id, server_id=server_id) for server_id in server_ids]
            )
            await self.session.flush()

    async def agent_exists(self, agent_id: str, user_id: str) -> bool:
        exists_query = exists("*").select_from(Agent)
        if agent_id:
            exists_query = exists_query.where(Agent.id == agent_id)
        if user_id:
            exists_query = exists_query.where(Agent.user_id == user_id)
        query = select(exists_query)
        return await self.session.scalar(query)

    @classmethod
    def get_new_instance(cls, session: AsyncSession = Depends(get_session)) -> Self:
        return cls(session)
