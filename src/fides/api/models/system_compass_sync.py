from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class SystemCompassSync(Base):
    """A record of systems updated via Compass sync"""

    @declared_attr
    def __tablename__(self) -> str:
        return "system_compass_sync"

    sync_started_at = Column(DateTime(timezone=True))
    sync_completed_at = Column(DateTime(timezone=True))

    updated_systems = Column(MutableList.as_mutable(ARRAY(String)))

    @classmethod
    def start_system_sync(cls, db: Session) -> "SystemCompassSync":
        return SystemCompassSync(sync_started_at=datetime.utcnow()).save(db=db)  # type: ignore[return-value]

    def finish_system_sync(
        self, db: Session, updated_systems: List[str]
    ) -> "SystemCompassSync":
        self.updated_systems = updated_systems
        self.sync_completed_at = datetime.utcnow()
        return self.save(db=db)  # type: ignore[return-value]
