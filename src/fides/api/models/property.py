from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db import session
from fides.api.db.base_class import Base
from fides.api.schemas.property import PropertyType
from fides.config import get_config

CONFIG = get_config()


class Property(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_property"

    key = Column(String, index=True, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)

    @classmethod
    def create(
        cls, db: session, *, data: Dict[str, Any], check_name: bool = True
    ) -> Property:
        name: str = data.get("name")
        property_type: PropertyType = data.get("type")
        data["type"] = property_type.value
        data["key"] = re.sub(r"\s+", "_", name.lower().strip())
        return super().create(db=db, data=data, check_name=check_name)
