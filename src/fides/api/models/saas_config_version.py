from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class SaaSConfigVersion(Base):
    """
    Stores a snapshot of each SaaS integration config and dataset per version.

    A new row is upserted whenever a SaaS integration version is seen for the
    first time — on startup (for bundled OOB connectors), on custom template
    upload/update, or on direct SaaS config PATCH.  Rows are never deleted so
    that execution logs can always resolve the config/dataset that was active
    when a DSR ran.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "saas_config_version"

    __table_args__ = (
        # is_custom is part of the key: the same version string can exist once
        # as an OOB template and once as a custom override without conflict.
        UniqueConstraint(
            "connector_type", "version", "is_custom", name="uq_saas_config_version"
        ),
    )

    connector_type = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    config = Column(JSONB, nullable=False)
    dataset = Column(JSONB, nullable=True)
    is_custom = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<SaaSConfigVersion(connector_type='{self.connector_type}', version='{self.version}', is_custom={self.is_custom})>"

    @classmethod
    def upsert(
        cls,
        db: Session,
        connector_type: str,
        version: str,
        config: Dict[str, Any],
        dataset: Optional[Dict[str, Any]] = None,
        is_custom: bool = False,
    ) -> "SaaSConfigVersion":
        """
        Insert or update a version snapshot.

        - OOB rows (is_custom=False): treated as immutable once written — the
          version string is controlled by Ethyca and the content never changes
          for a given version.
        - Custom rows (is_custom=True): config/dataset are updated in place so
          that users can iterate on a custom template without bumping the version.
        """
        existing = (
            db.query(cls)
            .filter(
                cls.connector_type == connector_type,
                cls.version == version,
                cls.is_custom == is_custom,
            )
            .first()
        )

        if existing:
            if is_custom:
                existing.config = config
                existing.dataset = dataset
                db.add(existing)
                db.commit()
                db.refresh(existing)
            return existing

        return cls.create(
            db=db,
            data={
                "connector_type": connector_type,
                "version": version,
                "config": config,
                "dataset": dataset,
                "is_custom": is_custom,
            },
        )
