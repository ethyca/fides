import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from fides.api.db.base_class import Base


class SystemConnectionLinkType(str, enum.Enum):
    """Qualifies the purpose of a system-to-integration association."""

    dsr = "dsr"
    monitoring = "monitoring"


class SystemConnectionConfigLink(Base):
    """
    Join table that links a System to a ConnectionConfig with a qualified
    relationship type. Supports one:many and many:many associations and
    distinguishes the purpose of each link (e.g. DSR vs. monitoring).
    """

    __tablename__ = "system_connection_config_link"

    system_id = Column(
        String,
        ForeignKey("ctl_systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connection_config_id = Column(
        String,
        ForeignKey("connectionconfig.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    link_type = Column(
        Enum(SystemConnectionLinkType),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    system = relationship("System")
    connection_config = relationship("ConnectionConfig")

    __table_args__ = (
        UniqueConstraint(
            "system_id",
            "connection_config_id",
            "link_type",
            name="uq_system_connconfig_link_type",
        ),
    )
