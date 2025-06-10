from typing import Self

from fastapi import Depends
from sqlalchemy import Select

from .repository import UserRepository
from .schemas import UserCreate
from .schemas import UserUpdate
from src.agents.repository import AgentRepository
from src.agents.schemas import AgentCreate
from src.agents.schemas import AgentData
from src.darp_servers.registry_client import RegistryClient
from src.darp_servers.repository import DARPServerRepository
from src.database import User
from src.errors import InvalidData
from src.errors import NotAllowedError
from src.errors import NotFoundError
from src.settings import settings


class UserService:
    def __init__(
        self,
        repo: UserRepository,
        agent_repo: AgentRepository,
        server_repo: DARPServerRepository,
        registry_client: RegistryClient,
    ) -> None:
        self.repo = repo
        self.agent_repo = agent_repo
        self.server_repo = server_repo
        self.registry_client = registry_client

    async def get_single_user(
        self, user_id: str | None = None, username: str | None = None, email: str | None = None
    ) -> User:
        if not (user_id or username or email):
            raise InvalidData("No parameters present")
        user = await self.repo.get_user(user_id=user_id, username=username, email=email)
        if not user:
            raise NotFoundError(message="User does not exist")
        return user

    async def get_users(self) -> Select:
        return await self.repo.get_users()

    async def update_user(self, user_id: str, data: UserUpdate) -> User:
        if user_id != data.current_user_id:
            raise NotAllowedError("Not allowed")
        user_exists = await self.repo.user_exists(user_id=user_id)
        if not user_exists:
            raise NotFoundError(message="User with this id does not exist")
        updated_user_exists = await self.repo.updated_user_exists(update_data=data.update_data)
        if updated_user_exists:
            raise InvalidData("This username or email is already in use")
        user = await self.repo.update_user(user_id=user_id, data=data.update_data)
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        user = await self.repo.create_user(user_data)
        servers = await self.registry_client.get_servers_by_id(server_ids=settings.DEFAULT_AGENT_SERVER_IDS)
        await self.server_repo.upsert_servers(servers=servers)
        default_agent_data = AgentCreate(
            current_user_id=user.id,
            agent_data=AgentData(name=settings.DEFAULT_AGENT_NAME, description=settings.DEFAULT_AGENT_DESCRIPTION),
            server_ids=settings.DEFAULT_AGENT_SERVER_IDS,
        )
        await self.agent_repo.create_agent(
            creation_data=default_agent_data,
            server_ids=[str(server_id) for server_id in settings.DEFAULT_AGENT_SERVER_IDS],
        )
        return user

    async def delete_user(self, user_id: str) -> None:
        await self.repo.delete_user(user_id)

    @classmethod
    def get_new_instance(
        cls,
        repo: UserRepository = Depends(UserRepository.get_new_instance),
        agent_repo: AgentRepository = Depends(AgentRepository.get_new_instance),
        server_repo: DARPServerRepository = Depends(DARPServerRepository.get_new_instance),
        registry_client: RegistryClient = Depends(RegistryClient.get_new_instance),
    ) -> Self:
        return cls(repo=repo, agent_repo=agent_repo, server_repo=server_repo, registry_client=registry_client)
