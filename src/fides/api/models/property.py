from __future__ import annotations

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.schemas.property import PropertyType
from fides.config import get_config

CONFIG = get_config()


class Property(Base):
    """
    This class serves as a model for digital properties, such as websites or other online platforms.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_property"

    key = Column(String, index=True, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(EnumColumn(PropertyType), nullable=False)
