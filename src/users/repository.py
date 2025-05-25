from typing import Self

from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy import exists
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import UserCreate
from .schemas import UserUpdateData
from src.database import get_session
from src.database import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user(self, user_id: str | None = None, wallet_address: str | None = None) -> User | None:
        assert user_id or wallet_address, "Incorrect params"
        query = select(User)
        if user_id:
            query = query.where(User.id == user_id)
        if wallet_address:
            query = query.where(User.wallet_address == wallet_address)
        user = (await self.session.execute(query)).scalar_one_or_none()
        return user

    @staticmethod
    async def get_users() -> Select:
        query = select(User).order_by(User.created_at)
        return query

    async def create_user(self, user: UserCreate) -> User:
        user = User(**user.model_dump())
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_user(self, data: UserUpdateData, user_id: str) -> User:
        update_data: dict = data.model_dump(exclude_none=True)
        user = await self.get_user(user_id=user_id)
        assert user, "Missing existence check"
        for k, v in update_data.items():
            setattr(user, k, v)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: str) -> None:
        query = delete(User).where(User.id == user_id)
        await self.session.execute(query)

    async def user_exists(self, user_id: str | None = None, wallet_address: str | None = None) -> bool:
        assert user_id or wallet_address, "Incorrect params"
        exists_query = exists("*").select_from(User)
        if user_id:
            exists_query = exists_query.where(User.id == user_id)
        if wallet_address:
            exists_query = exists_query.where(User.wallet_address == wallet_address)
        query = select(exists_query)
        return await self.session.scalar(query)

    @classmethod
    def get_new_instance(cls, session: AsyncSession = Depends(get_session)) -> Self:
        return cls(session)
