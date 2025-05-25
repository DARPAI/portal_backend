from typing import Self

from fastapi import Depends
from sqlalchemy import Select

from .repository import AgentRepository
from .schemas import AgentCreate
from .schemas import AgentUpdate
from src.darp_servers.registry_client import RegistryClient
from src.darp_servers.repository import DARPServerRepository
from src.database import Agent
from src.errors import NotFoundError


class AgentService:
    def __init__(
        self, repo: AgentRepository, server_repo: DARPServerRepository, registry_client: RegistryClient
    ) -> None:
        self.repo = repo
        self.server_repo = server_repo
        self.registry_client = registry_client

    async def get_single_agent(self, agent_id: str, current_user_id: str) -> Agent:
        agent = await self.repo.get_agent(agent_id=agent_id, user_id=current_user_id)
        if not agent:
            raise NotFoundError(message="Agent with this id does not exist")
        return agent

    async def get_agents(self, user_id: str | None) -> Select:
        return await self.repo.get_agents(user_id=user_id)

    async def update_agent(self, agent_id: str, data: AgentUpdate) -> Agent:
        if not await self.repo.agent_exists(agent_id=agent_id, user_id=data.current_user_id):
            raise NotFoundError(message="Agent with this id does not exist")
        if data.server_ids:
            servers = await self.registry_client.get_servers_by_id(server_ids=data.server_ids)
            await self.server_repo.upsert_servers(servers=servers)
        string_ids = [str(server_id) for server_id in data.server_ids or []]
        agent = await self.repo.update_agent(agent_id=agent_id, data=data.agent_data, server_ids=string_ids)
        return agent

    async def create_agent(self, data: AgentCreate) -> Agent:
        if data.server_ids:
            servers = await self.registry_client.get_servers_by_id(server_ids=data.server_ids)
            await self.server_repo.upsert_servers(servers=servers)
        string_ids = [str(server_id) for server_id in data.server_ids]
        agent = await self.repo.create_agent(data, server_ids=string_ids)
        return agent

    async def delete_agent(self, agent_id: str, current_user_id: str) -> None:
        agent = await self.repo.agent_exists(agent_id=agent_id, user_id=current_user_id)
        if not agent:
            raise NotFoundError(message="Agent with this id does not exist")
        await self.repo.delete_agent(agent_id=agent_id)

    @classmethod
    def get_new_instance(
        cls,
        repo: AgentRepository = Depends(AgentRepository.get_new_instance),
        server_repo: DARPServerRepository = Depends(DARPServerRepository.get_new_instance),
        registry_client: RegistryClient = Depends(RegistryClient.get_new_instance),
    ) -> Self:
        return cls(repo=repo, server_repo=server_repo, registry_client=registry_client)
