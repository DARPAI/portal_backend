from fastapi import Depends

from .repository import UserRepository
from src.errors import NotFoundError


async def existing_user_id(user_id: str, repo: UserRepository = Depends(UserRepository.get_new_instance)) -> str:
    user = await repo.user_exists(user_id)
    if not user:
        raise NotFoundError(message="User with this id does not exist")
    return user_id


async def valid_current_user_id(
    current_user_id: str, repo: UserRepository = Depends(UserRepository.get_new_instance)
) -> str:
    user = await repo.user_exists(current_user_id)
    if not user:
        raise NotFoundError(message="User with this id does not exist")
    return current_user_id
