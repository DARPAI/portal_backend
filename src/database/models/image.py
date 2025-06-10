from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import HasCreatedAt
from .mixins import HasId


class Image(HasId, HasCreatedAt, Base):
    __tablename__ = "images"

    url: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    original_url: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str | None] = mapped_column(String, nullable=True)
    width: Mapped[int] = mapped_column("w", nullable=False)
    height: Mapped[int] = mapped_column("h", nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<Image(url='{self.url}', width={self.width}, height={self.height})>"
