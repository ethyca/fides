from enum import Enum as EnumType
from sqlalchemy import Column, String, Enum as EnumColumn

from fidesops.db.base_class import Base


class AuditLogAction(EnumType):
    """Enum for audit log actions, reflecting what a  user did"""

    approved = "approved"
    denied = "denied"


class AuditLog(Base):
    """The log of all user actions within the system"""

    user_id = Column(String, nullable=True, index=True)
    privacy_request_id = Column(String, nullable=True, index=True)
    action = Column(
        EnumColumn(AuditLogAction),
        index=True,
        nullable=False,
    )
    message = Column(String, nullable=True)
