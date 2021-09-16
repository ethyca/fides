from sqlalchemy import Column, Text

from .modelbase import SqlAlchemyBase
from .fides_base import FidesBase


class DataCategory(SqlAlchemyBase, FidesBase):

    __tablename__ = "data_category"

    parent_key = Column(Text(length=100))
