from typing import Self

from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy import exists
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgresql_upsert
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import DARPServerCreate
from .schemas import RegistryServerSchema
from src.database import agents_darp_servers
from src.database import DARPServer
from src.database import get_session


class DARPServerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_server(self, server_id: str | None = None, name: str | None = None) -> DARPServer | None:
        assert server_id or name, "Incorrect params"
        query = select(DARPServer)
        if server_id:
            query = query.where(DARPServer.id == server_id)
        if name:
            query = query.where(DARPServer.name == name)
        server = (await self.session.execute(query)).scalar_one_or_none()
        return server

    @staticmethod
    async def get_servers() -> Select:
        query = select(DARPServer).order_by(DARPServer.name)
        return query

    async def get_servers_by_agent(self, agent_id: str) -> list[DARPServer]:
        query = (
            select(DARPServer).join(agents_darp_servers).where(agents_darp_servers.c.agent_id == agent_id)  # type: ignore
        )
        servers = await self.session.execute(query)
        return list(servers.scalars().all())

    async def upsert_servers(self, servers: list[RegistryServerSchema]) -> None:
        if not servers:
            return
        query = postgresql_upsert(DARPServer).values([server.model_dump() for server in servers])
        query = query.on_conflict_do_update(
            index_elements=[DARPServer.id],
            set_=dict(
                name=query.excluded.name,
                description=query.excluded.description,
                url=query.excluded.url,
                logo=query.excluded.logo,
                tools=query.excluded.tools,
            ),
        )
        await self.session.execute(query)

    async def get_servers_by_ids(self, server_ids: list[str]) -> list[DARPServer]:
        query = select(DARPServer).where(DARPServer.id.in_(server_ids))
        servers = await self.session.execute(query)
        return list(servers.scalars().all())

    async def create_server(self, creation_data: DARPServerCreate) -> DARPServer:
        arp_server = DARPServer(**creation_data.model_dump(exclude_none=True))
        self.session.add(arp_server)
        await self.session.flush()
        await self.session.refresh(arp_server)
        return arp_server

    async def delete_server(self, server_id: str) -> None:
        query = delete(DARPServer).where(DARPServer.id == server_id)
        await self.session.execute(query)

    async def server_exists(self, server_id: str | None = None, name: str | None = None) -> bool:
        assert server_id or name, "Invalid params"
        exists_query = exists("*").select_from(DARPServer)
        if server_id:
            exists_query = exists_query.where(DARPServer.id == server_id)
        if name:
            exists_query = exists_query.where(DARPServer.name == name)
        query = select(exists_query)
        return await self.session.scalar(query)

    @classmethod
    def get_new_instance(cls, session: AsyncSession = Depends(get_session)) -> Self:
        return cls(session)
