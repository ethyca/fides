from enum import Enum
from typing import Optional, Union

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.models.digest.conditional_dependencies import DigestConditionType
from fides.api.schemas.messaging.messaging import MessagingMethod
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
)


class DigestType(str, Enum):
    """Types of digests that can be configured."""

    MANUAL_TASKS = "manual_tasks"
    PRIVACY_REQUESTS = "privacy_requests"
    # More types can be added here


class DigestConfig(Base):
    """Generic configuration for any type of digest."""

    @declared_attr
    def __tablename__(cls) -> str:
        return "digest_config"

    # Digest identification
    digest_type = Column(EnumColumn(DigestType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    messaging_service_type = Column(
        EnumColumn(MessagingMethod),
        nullable=False,
        default=MessagingMethod.EMAIL,
        index=True,
    )
    cron_expression = Column(String(100), nullable=False, default="0 9 * * 1")
    timezone = Column(String(50), nullable=False, default="US/Eastern")
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    next_scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    config_metadata = Column(JSONB, nullable=True, default={})

    def get_receiver_conditions(
        self, db: Session
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get receiver conditions for this digest config."""
        raise NotImplementedError("Conditions are not implemented for digests")

    def get_content_conditions(
        self, db: Session
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get content conditions for this digest config."""
        raise NotImplementedError("Conditions are not implemented for digests")

    def get_priority_conditions(
        self, db: Session
    ) -> Optional[Union[ConditionLeaf, ConditionGroup]]:
        """Get priority conditions for this digest config."""
        raise NotImplementedError("Conditions are not implemented for digests")

    def get_all_conditions(
        self, db: Session
    ) -> dict["DigestConditionType", Optional[Condition]]:
        """Get all condition types for this digest config."""
        raise NotImplementedError("Conditions are not implemented for digests")
