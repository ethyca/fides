from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import Base


class SystemHistory(Base):
    """History of changes to a system"""

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_system_history"

    edited_by = Column(String, nullable=True)
    system_id = Column(
        String, ForeignKey("ctl_systems.id", ondelete="cascade"), nullable=False
    )
    before = Column(MutableDict.as_mutable(JSONB), nullable=False)
    after = Column(MutableDict.as_mutable(JSONB), nullable=False)
