from typing import Any

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base


class DataConsumer(Base):
    """
    Non-system data consumers (groups, projects, custom types).
    System-type consumers are surfaced via a facade over ctl_systems.
    """

    __tablename__ = "data_consumer"
    __table_args__ = (
        CheckConstraint("type != 'system'", name="ck_data_consumer_not_system"),
    )

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False, index=True)
    external_id = Column(String, nullable=True)
    egress = Column(JSON, nullable=True)
    ingress = Column(JSON, nullable=True)
    data_shared_with_third_parties = Column(Boolean, server_default="f", nullable=False)
    third_parties = Column(String, nullable=True)
    shared_categories = Column(ARRAY(String), server_default="{}", nullable=False)
    contact_email = Column(String, nullable=True)
    contact_slack_channel = Column(String, nullable=True)
    contact_details = Column(JSON, nullable=True)
    tags = Column(ARRAY(String), server_default="{}", nullable=False)

    consumer_purposes = relationship(
        "DataConsumerPurpose",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = False,
    ) -> "DataConsumer":
        """Override create to skip name uniqueness check.
        Multiple consumers can share a name."""
        return super().create(db=db, data=data, check_name=check_name)


class DataConsumerPurpose(Base):
    """
    Audited join table linking a non-system DataConsumer to a DataPurpose.
    """

    __tablename__ = "data_consumer_purpose"
    __table_args__ = (
        UniqueConstraint(
            "data_consumer_id", "data_purpose_id", name="uq_data_consumer_purpose"
        ),
    )

    data_consumer_id = Column(
        String,
        ForeignKey("data_consumer.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_purpose_id = Column(
        String,
        ForeignKey("data_purpose.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_by = Column(
        String,
        ForeignKey("fidesuser.id"),
        nullable=True,
    )

    data_consumer = relationship("DataConsumer", lazy="selectin")
    data_purpose = relationship("DataPurpose", lazy="selectin")
