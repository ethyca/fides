from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.models.sql_models import System


class SystemHistory(Base):
    """History of changes to a system"""

    @declared_attr
    def __tablename__(self) -> str:
        return "system_history"

    edited_by = Column(String, nullable=False)
    system_key = Column(
        String, ForeignKey("ctl_systems.fides_key", ondelete="cascade"), nullable=False
    )
    before = Column(MutableDict.as_mutable(JSONB), nullable=False)
    after = Column(MutableDict.as_mutable(JSONB), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class Config:
        orm_mode = True
