from typing import Any, Dict, List, Optional

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class ConnectionConfigSaaSHistory(Base):
    """
    Append-only snapshot of a connection's SaaS config taken each time
    ConnectionConfig.update_saas_config() is called.

    Unlike SaaSConfigVersion (which stores one row per connector_type/version),
    this table is scoped to an individual ConnectionConfig instance.  It captures
    divergent configs — e.g. when a connection is individually PATCHed to a
    version that differs from the shared template.

    connection_key is denormalized so that history is still queryable if the
    parent ConnectionConfig row is deleted (FK uses ON DELETE SET NULL).
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "connection_config_saas_history"

    connection_config_id = Column(
        String,
        ForeignKey("connectionconfig.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    connection_key = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    config = Column(JSONB, nullable=False)
    dataset = Column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ConnectionConfigSaaSHistory("
            f"connection_key='{self.connection_key}', "
            f"version='{self.version}', "
            f"id='{self.id}')>"
        )

    @classmethod
    def create_snapshot(
        cls,
        db: Session,
        connection_config_id: str,
        connection_key: str,
        version: str,
        config: Dict[str, Any],
        datasets: Optional[List[Dict[str, Any]]] = None,
    ) -> "ConnectionConfigSaaSHistory":
        """
        Appends a new history row.  Always creates a new row — no upsert logic —
        so every write is preserved as a distinct audit entry.
        """
        return cls.create(
            db=db,
            data={
                "connection_config_id": connection_config_id,
                "connection_key": connection_key,
                "version": version,
                "config": config,
                "dataset": datasets or None,
            },
        )
