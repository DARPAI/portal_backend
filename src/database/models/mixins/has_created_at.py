from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.orm import declared_attr


@declarative_mixin
class HasCreatedAt:
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.now, nullable=False)
