from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base
from .mixins import HasCreatedAt
from .mixins import HasId
from .mixins import HasUpdatedAt


class Report(HasId, HasCreatedAt, HasUpdatedAt, Base):
    __tablename__ = "reports"

    message_id: Mapped[str] = mapped_column(ForeignKey("messages.id"))
    title: Mapped[str] = mapped_column(String(), nullable=False)
    text: Mapped[str] = mapped_column(Text(), nullable=False)
    creator_id: Mapped[str] = mapped_column(String(), nullable=False)
