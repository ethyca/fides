from typing import Optional

from sqlalchemy import Column, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base
from fides.api.models.fides_user import FidesUser
from fides.config import get_config

CONFIG = get_config()


class SystemHistory(Base):
    """History of changes to a system"""

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_system_history"

    user_id = Column(String, nullable=True)
    system_id = Column(
        String, ForeignKey("ctl_systems.id", ondelete="cascade"), nullable=False
    )
    before = Column(MutableDict.as_mutable(JSONB), nullable=False)
    after = Column(MutableDict.as_mutable(JSONB), nullable=False)

    __table_args__ = (
        Index(
            "idx_plus_system_history_created_at_system_id", "created_at", "system_id"
        ),
    )

    @property
    def edited_by(self) -> Optional[str]:
        """Derive the username from the user_id"""
        if not self.user_id:
            return None

        if self.user_id == CONFIG.security.oauth_root_client_id:
            return CONFIG.security.root_username

        db = Session.object_session(self)
        user: Optional[FidesUser] = FidesUser.get_by(db, field="id", value=self.user_id)

        return user.username if user else self.user_id
