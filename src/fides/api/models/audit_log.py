from enum import Enum as EnumType

from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import String

from fides.api.db.base_class import Base


class AuditLogAction(str, EnumType):
    """Enum for audit log actions, reflecting what a user did."""

    approved = "approved"
    denied = "denied"
    email_sent = "email_sent"
    finished = "finished"


class AuditLog(Base):
    """The log of all user actions within the system."""

    user_id = Column(String, nullable=True, index=True)
    privacy_request_id = Column(String, nullable=True, index=True)
    action = Column(
        EnumColumn(AuditLogAction),
        index=True,
        nullable=False,
    )
    message = Column(String, nullable=True)
    webhook_id = Column(String, nullable=True, index=True)
