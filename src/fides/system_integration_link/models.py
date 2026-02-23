from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from fides.api.db.base_class import Base


class SystemConnectionConfigLink(Base):
    """
    Join table that links a System to a ConnectionConfig.

    Current constraint: each ConnectionConfig may be linked to at most one
    System (enforced by a unique constraint on ``connection_config_id``).
    This may be relaxed in the future to support many-to-many if a concrete
    need arises (e.g. a single integration shared across multiple systems).

    Several parts of the codebase still treat the System ↔ ConnectionConfig
    relationship as 1:1 (``uselist=False`` on both sides of the SQLAlchemy
    relationship).  Before lifting the unique constraint, audit those call
    sites and the ``create_or_update_link`` helper below.

    Future: a ``link_type`` column (e.g. "dsr" vs "monitoring") could be
    added to distinguish the purpose of each link.  The unique constraint
    would need to be updated to include the new column.
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
        unique=True,
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

    __table_args__: tuple = ()

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
