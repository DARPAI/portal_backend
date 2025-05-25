from datetime import datetime

from src.base_schema import BaseSchema


class UserRead(BaseSchema):
    id: str
    is_registered: bool
    wallet_address: str | None
    updated_at: datetime
    created_at: datetime


class UserCreate(BaseSchema):
    wallet_address: str | None = None
    is_registered: bool = False


class UserUpdateData(BaseSchema):
    wallet_address: str | None = None
    is_registered: bool | None = None


class UserUpdate(BaseSchema):
    current_user_id: str
    update_data: UserUpdateData
