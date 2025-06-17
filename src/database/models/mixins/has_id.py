from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.orm import declared_attr

from src.database.id import generate_shortid


@declarative_mixin
class HasId:
    @declared_attr
    def id(cls):
        return Column(String, primary_key=True, default=generate_shortid, index=True, unique=True)
