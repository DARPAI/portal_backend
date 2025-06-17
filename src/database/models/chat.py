from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import HasCreatedAt
from .mixins import HasId
from .mixins import HasUpdatedAt
from .mixins import HasUserId


class Chat(HasId, HasUserId, HasCreatedAt, HasUpdatedAt, Base):
    __tablename__ = "chats"

    title: Mapped[str] = mapped_column(String, nullable=False, default="New Chat")
    agent_id: Mapped[str] = mapped_column(
        String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
