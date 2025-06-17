from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.orm import declared_attr


@declarative_mixin
class HasUserId:
    @declared_attr
    def user_id(cls):
        return Column(String, nullable=False, index=True)
