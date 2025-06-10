from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import HasCreatedAt
from .mixins import HasId
from .mixins import HasUpdatedAt


class User(HasId, HasCreatedAt, HasUpdatedAt, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=True, index=True)
    is_registered: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_email_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
