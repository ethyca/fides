from __future__ import annotations

import enum

from sqlalchemy import Column, Enum, String, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.common_exceptions import KeyValidationError
from fides.api.db.base_class import Base, FidesBase, OrmWrappedFidesBase

# pylint: disable=redefined-builtin


class CustomAssetType(enum.Enum):
    fides_css = "fides.css"


class CustomAsset(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_custom_asset"

    key = Column(
        Enum(CustomAssetType),
        index=True,
        nullable=False,
    )
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
