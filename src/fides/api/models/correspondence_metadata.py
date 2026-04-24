from enum import Enum as EnumType
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn

if TYPE_CHECKING:
    from fides.api.models.comment import Comment  # noqa: F401


class CorrespondenceDeliveryStatus(str, EnumType):
    """Delivery status for correspondence messages."""

    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    bounced = "bounced"
    failed = "failed"


class CorrespondenceMetadata(Base):
    """1:1 metadata for correspondence comments (delivery tracking, threading)."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "correspondence_metadata"

    comment_id = Column(
        String,
        ForeignKey("comment.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    message_id = Column(String, unique=True, index=True, nullable=False)
    in_reply_to = Column(String, nullable=True)
    reply_to_address = Column(String, index=True, nullable=True)
    delivery_status = Column(
        EnumColumn(CorrespondenceDeliveryStatus, native_enum=False),
        nullable=False,
        server_default=CorrespondenceDeliveryStatus.pending,
    )
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    bounce_reason = Column(String, nullable=True)
    sender_email = Column(String, nullable=True)
    recipient_email = Column(String, nullable=True)

    comment = relationship(
        "Comment",
        back_populates="correspondence_metadata",
        uselist=False,
    )
