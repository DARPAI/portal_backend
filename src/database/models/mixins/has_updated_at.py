from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.orm import declared_attr


@declarative_mixin
class HasUpdatedAt:
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, onupdate=datetime.now, default=datetime.now, nullable=False)
