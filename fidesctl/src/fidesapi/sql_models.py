from typing import Dict

from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects import mysql
import sqlalchemy.ext.declarative


class FidesBase:
    """The base SQL model for all Fides Resources."""

    id = Column(Integer, primary_key=True, index=True)
    fides_key = Column(mysql.VARCHAR(200), primary_key=True, index=True)
    organization_fides_key = Column(Text)
    name = Column(Text)
    description = Column(Text)


SqlAlchemyBase = sqlalchemy.ext.declarative.declarative_base(cls=FidesBase)


class DataCategory(SqlAlchemyBase):

    __tablename__ = "data_category"

    parent_key = Column(Text(length=100))


class DataSubject(SqlAlchemyBase):

    __tablename__ = "data_subject"


sql_model_map: Dict = {
    "data_category": DataCategory,
    "data_subject": DataSubject,
}
