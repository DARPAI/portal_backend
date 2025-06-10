from datetime import datetime

from src.base_schema import BaseSchema


class UserRead(BaseSchema):
    id: str
    is_registered: bool
    is_email_confirmed: bool
    username: str | None
    updated_at: datetime
    created_at: datetime


class UserProfile(UserRead):
    email: str | None


class UserAuth(UserProfile):
    hashed_password: str | None


class UserCreate(BaseSchema):
    is_registered: bool = False


class UserUpdateData(BaseSchema):
    username: str | None = None
    email: str | None = None
    hashed_password: str | None = None
    is_registered: bool | None = None
    is_email_confirmed: bool | None = None


class UserUpdate(BaseSchema):
    current_user_id: str
    update_data: UserUpdateData
