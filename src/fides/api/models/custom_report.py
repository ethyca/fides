from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import Base  # type: ignore[attr-defined]
from fides.api.models.fides_user import FidesUser


class CustomReport(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "plus_custom_report"

    name = Column(String, unique=True)
    type = Column(String, nullable=False)
    created_by = Column(
        String,
        ForeignKey(FidesUser.id_field_path, ondelete="SET NULL"),
        nullable=True,
    )
    config = Column(MutableDict.as_mutable(JSONB))
