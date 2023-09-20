from enum import Enum

from sqlalchemy import Column, Text
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn


class CustomAssetType(str, Enum):
    fides_css = "fides_css"


class CustomAsset(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_custom_asset"

    asset_type = Column(
        EnumColumn(CustomAssetType), index=True, unique=True, nullable=False
    )
    content = Column(Text, nullable=False)
