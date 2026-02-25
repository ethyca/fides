from enum import Enum as EnumType

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base


class SystemConnectionLinkType(str, EnumType):
    """
    Enum for system-connection link types. Indicates the purpose of the link.

    - dsr: Link for Data Subject Request (DSR) operations
    - monitoring: Link for monitoring/discovery operations
    """

    dsr = "dsr"
    monitoring = "monitoring"


class SystemConnectionConfigLink(Base):
    """
    Join table that links Systems to ConnectionConfigs with a qualified relationship type.

    This enables a System to have multiple ConnectionConfigs with different purposes
    (e.g., one for DSR operations, another for monitoring).
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
