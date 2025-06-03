from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from fastapi_pagination import add_pagination
from fastapi_pagination import Page
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from .dependencies import existing_user_id
from .schemas import UserAuth
from .schemas import UserCreate
from .schemas import UserRead
from .schemas import UserUpdate
from .service import UserService
from src.database import get_session
from src.database import User

router = APIRouter(prefix="/users")

add_pagination(router)


@router.get("/{user_id}", response_model=UserRead)
async def get_single_user(user_id: str, service: UserService = Depends(UserService.get_new_instance)) -> User:
    return await service.get_single_user(user_id=user_id)


@router.get("/", response_model=UserAuth)
async def get_user_by_metadata(
    user_id: str | None = None,
    username: str | None = None,
    email: str | None = None,
    service: UserService = Depends(UserService.get_new_instance),
) -> User:
    user = await service.get_single_user(user_id=user_id, username=username, email=email)
    return user


@router.get("/list", response_model=Page[UserRead])
async def list_users(
    params: Params = Depends(),
    session: AsyncSession = Depends(get_session),
    service: UserService = Depends(UserService.get_new_instance),
) -> Page[User]:
    users_query: Select = await service.get_users()
    return await paginate(session, users_query, params)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserRead)
async def create_user(data: UserCreate, service: UserService = Depends(UserService.get_new_instance)) -> User:
    return await service.create_user(user_data=data)


@router.put("/{user_id}", response_model=UserAuth)
async def update_agent(
    user_id: str, data: UserUpdate, service: UserService = Depends(UserService.get_new_instance)
) -> User:
    return await service.update_user(data=data, user_id=user_id)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str = Depends(existing_user_id), service: UserService = Depends(UserService.get_new_instance)
) -> None:
    return await service.delete_user(user_id=user_id)
