from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from fides.api.db.base_class import Base


class SystemConnectionConfigLink(Base):
    """
    Join table that links a System to a ConnectionConfig.

    Supports one:many and many:many associations between systems and
    integrations. Currently enforced as one:one at the application level.
    """

    __tablename__ = "system_connection_config_link"  # type: ignore[assignment]

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

    system = relationship("System")  # type: ignore[misc]
    connection_config = relationship("ConnectionConfig")  # type: ignore[misc]

    __table_args__ = (
        UniqueConstraint(
            "system_id",
            "connection_config_id",
            name="uq_system_connconfig_link",
        ),
    )

    @classmethod
    def create_or_update_link(
        cls,
        db: Session,
        system_id: str,
        connection_config_id: str,
    ) -> SystemConnectionConfigLink:
        """Replace any existing link for this connection_config with a new one.

        Ensures at most one system link per connection config.
        """
        db.query(cls).filter(cls.connection_config_id == connection_config_id).delete(
            synchronize_session="evaluate"
        )

        link = cls(
            system_id=system_id,
            connection_config_id=connection_config_id,
        )
        db.add(link)
        db.flush()
        return link
