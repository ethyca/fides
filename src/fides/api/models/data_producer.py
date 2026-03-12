from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.detection_discovery import MonitorConfig
    from fides.api.models.fides_user import FidesUser


class DataProducer(Base):
    """
    Represents a team or group responsible for data registration
    and purpose assignment to datasets.
    """

    __tablename__ = "data_producer"

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    external_id = Column(String, nullable=True)
    monitor_id = Column(
        String,
        ForeignKey("monitorconfig.id"),
        nullable=True,
    )
    contact_email = Column(String, nullable=True)
    contact_slack_channel = Column(String, nullable=True)
    contact_details = Column(JSON, nullable=True)

    members = relationship(
        "DataProducerMember",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    monitor = relationship("MonitorConfig", lazy="selectin")

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "DataProducer":
        """Override create to skip name uniqueness check.
        Multiple producers can share a name."""
        return super().create(db=db, data=data, check_name=check_name)


class DataProducerMember(Base):
    """
    Join table linking a DataProducer to FidesUser members.
    """

    __tablename__ = "data_producer_member"
    __table_args__ = (
        UniqueConstraint("data_producer_id", "user_id", name="uq_data_producer_member"),
    )

    data_producer_id = Column(
        String,
        ForeignKey("data_producer.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String,
        ForeignKey("fidesuser.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    data_producer = relationship("DataProducer", lazy="selectin")
    user = relationship("FidesUser", lazy="selectin")
