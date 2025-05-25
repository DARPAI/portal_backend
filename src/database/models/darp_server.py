from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import HasUpdatedAt


class DARPServer(HasUpdatedAt, Base):
    # Haven't renamed yet because it requires either db wipe or a complicated migration
    __tablename__ = "arp_servers"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    logo: Mapped[str | None] = mapped_column(String, nullable=True)
    tools: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
