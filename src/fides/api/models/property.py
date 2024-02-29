from __future__ import annotations

import random
import string

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

    def generate_id(self) -> str:
        """
        Generate a unique ID in the format 'FDS-XXXXXX' using uppercase alphanumeric characters.
        """
        characters = string.ascii_uppercase + string.digits
        return "FDS-" + "".join(random.choices(characters, k=6))

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_property"

    id = Column(
        String,
        primary_key=True,
        default=generate_id,
    )
    name = Column(String, nullable=False, unique=True)
    type = Column(EnumColumn(PropertyType), nullable=False)
