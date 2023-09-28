from __future__ import annotations

from sqlalchemy import Column, Enum, String, Text
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base
from fides.api.schemas.custom_asset import CustomAssetType


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
