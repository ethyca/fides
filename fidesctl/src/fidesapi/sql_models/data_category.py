from sqlalchemy import Column, String


from fidesapi.database import Base

from models.fides_base import FidesBase


class DataCategory(Base, FidesBase):

    __tablename__ = "data_category"

    parent_key = Column(String)
