from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import HasCreatedAt
from .mixins import HasId
from .mixins import HasUserId
from src.messages.types import MessageSource


class Message(HasId, HasUserId, HasCreatedAt, Base):
    __tablename__ = "messages"

    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[MessageSource] = mapped_column(String, nullable=False)
    content: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
