from typing import Self

from httpx import AsyncClient
from httpx import Response

from .schemas import RegistryServerSchema
from src.errors import InvalidData
from src.errors import RemoteServerError
from src.logger import logger
from src.settings import settings


class RegistryClient:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def get_servers_by_id(self, server_ids: list[int]) -> list[RegistryServerSchema]:
        if not server_ids:
            return []
        response = await self.client.get(url="/servers/batch", params=dict(ids=server_ids))
        if response.status_code == 400:
            raise InvalidData("One or more servers ids are invalid")
        if response.status_code != 200:
            logger.error(f"Registry respond with status code {response.status_code}, detail: {response.content}")
            raise RemoteServerError("Error getting server from registry")
        return self._collect_servers(response)

    async def get_fitting_servers(self, query: str):
        response = await self.client.get(url="/servers/search", params=dict(query=query))
        if response.status_code != 200:
            logger.error(f"Registry request failed. {response.status_code=}, {response.content=}")
            raise RemoteServerError("Error getting server info")
        return self._collect_servers(response)

    @staticmethod
    def _collect_servers(response: Response) -> list[RegistryServerSchema]:
        servers = response.json()
        logger.debug(servers)
        result = []
        for server in servers:
            result.append(RegistryServerSchema.model_validate(server))
        return result

    @classmethod
    def get_new_instance(cls) -> Self:
        return cls(client=AsyncClient(base_url=settings.REGISTRY_URL, timeout=30))
