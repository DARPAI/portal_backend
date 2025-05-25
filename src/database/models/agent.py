from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from .base import Base
from .mixins import HasCreatedAt
from .mixins import HasId
from .mixins import HasUserId
from src.settings import settings
from src.types import LLMProvider


agents_darp_servers = Table(
    "agents_arp_servers",
    Base.metadata,
    Column("agent_id", String, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("server_id", String, ForeignKey("arp_servers.id", ondelete="CASCADE"), primary_key=True),
)


class Agent(HasId, HasUserId, HasCreatedAt, Base):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(String, nullable=False)
    avatar_url: Mapped[str] = mapped_column(String, nullable=False, default=settings.DEFAULT_AVATAR_URL)
    provider: Mapped[LLMProvider] = mapped_column(String, nullable=False, default="")
    model: Mapped[str] = mapped_column(String, nullable=False)

    darp_servers = relationship("DARPServer", secondary="agents_arp_servers")
