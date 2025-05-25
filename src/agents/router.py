from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from fastapi_pagination import add_pagination
from fastapi_pagination import Page
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import AgentCreate
from .schemas import AgentRead
from .schemas import AgentUpdate
from .schemas import AgentWithServers
from .service import AgentService
from src.database import Agent
from src.database import get_session
from src.users.dependencies import valid_current_user_id

router = APIRouter(prefix="/agents")

add_pagination(router)


@router.get("/{agent_id}", response_model=AgentWithServers)
async def get_single_agent(
    agent_id: str,
    current_user_id: str = Depends(valid_current_user_id),
    service: AgentService = Depends(AgentService.get_new_instance),
) -> Agent:
    return await service.get_single_agent(agent_id=agent_id, current_user_id=current_user_id)


@router.put("/{agent_id}", response_model=AgentWithServers)
async def update_agent(
    agent_id: str, data: AgentUpdate, service: AgentService = Depends(AgentService.get_new_instance)
) -> Agent:
    return await service.update_agent(agent_id=agent_id, data=data)


@router.get("/", response_model=Page[AgentRead])
async def list_agents(
    current_user_id: str = Depends(valid_current_user_id),
    params: Params = Depends(),
    session: AsyncSession = Depends(get_session),
    service: AgentService = Depends(AgentService.get_new_instance),
) -> Page[Agent]:
    query: Select = await service.get_agents(user_id=current_user_id)
    return await paginate(session, query, params)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AgentWithServers)
async def create_agent(data: AgentCreate, service: AgentService = Depends(AgentService.get_new_instance)) -> Agent:
    return await service.create_agent(data=data)


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user_id: str = Depends(valid_current_user_id),
    service: AgentService = Depends(AgentService.get_new_instance),
) -> None:
    return await service.delete_agent(agent_id=agent_id, current_user_id=current_user_id)
