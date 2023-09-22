import enum

from sqlalchemy import Column, Enum, Text
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base


class CustomAssetType(enum.Enum):
    fides_css = "fides.css"


class CustomAsset(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_custom_asset"

    key = Column(
        Enum(*[e.value for e in CustomAssetType], name="customassettype"),
        index=True,
        nullable=False,
    )
    content = Column(Text, nullable=False)
