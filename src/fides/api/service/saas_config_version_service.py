from typing import List, Optional

from sqlalchemy.orm import Session

from fides.api.models.connection_config_saas_history import ConnectionConfigSaaSHistory
from fides.api.models.saas_config_version import SaaSConfigVersion
from fides.api.schemas.saas.saas_config import SaaSConfig


class SaaSConfigVersionService:
    """
    Service layer for SaaSConfigVersion read and write operations.

    Centralises all DB access for the saas_config_version table so that
    route handlers and models stay thin.
    """

    @staticmethod
    def record_template_version(
        db: Session,
        saas_config: SaaSConfig,
        is_custom: bool = False,
    ) -> SaaSConfigVersion:
        """
        Upsert a version snapshot for a connector template.

        Called from the PATCH saas-config route after the connection config is
        updated, so the table always reflects the latest config seen for each
        (connector_type, version) pair.
        """
        return SaaSConfigVersion.upsert(
            db=db,
            connector_type=saas_config.type,
            version=saas_config.version,
            config=saas_config.model_dump(mode="json"),
            dataset=None,  # PATCH only updates the config; dataset is managed separately
            is_custom=is_custom,
        )

    @staticmethod
    def list_versions(
        db: Session,
        connector_type: str,
    ) -> List[SaaSConfigVersion]:
        """
        Return all stored versions for a connector type, newest first.
        """
        return (
            db.query(SaaSConfigVersion)
            .filter(SaaSConfigVersion.connector_type == connector_type)
            .order_by(SaaSConfigVersion.created_at.desc())
            .all()
        )

    @staticmethod
    def get_version(
        db: Session,
        connector_type: str,
        version: str,
    ) -> Optional[SaaSConfigVersion]:
        """
        Return the most recent stored row for (connector_type, version).

        When both an OOB row (is_custom=False) and a custom row (is_custom=True)
        exist for the same version string, the one created most recently is
        returned. Callers that need to distinguish OOB from custom should filter
        on is_custom before calling this method.
        """
        return (
            db.query(SaaSConfigVersion)
            .filter(
                SaaSConfigVersion.connector_type == connector_type,
                SaaSConfigVersion.version == version,
            )
            .order_by(SaaSConfigVersion.created_at.desc())
            .first()
        )

    @staticmethod
    def list_connection_history(
        db: Session,
        connection_config_id: str,
    ) -> List[ConnectionConfigSaaSHistory]:
        """Return all per-connection SaaS config snapshots, ordered newest first."""
        return (
            db.query(ConnectionConfigSaaSHistory)
            .filter(
                ConnectionConfigSaaSHistory.connection_config_id == connection_config_id
            )
            .order_by(ConnectionConfigSaaSHistory.created_at.desc())
            .all()
        )

    @staticmethod
    def get_connection_history_by_version(
        db: Session,
        connection_config_id: str,
        version: str,
    ) -> Optional[ConnectionConfigSaaSHistory]:
        """Return the most recent snapshot for a given connection and version."""
        return (
            db.query(ConnectionConfigSaaSHistory)
            .filter(
                ConnectionConfigSaaSHistory.connection_config_id
                == connection_config_id,
                ConnectionConfigSaaSHistory.version == version,
            )
            .order_by(ConnectionConfigSaaSHistory.created_at.desc())
            .first()
        )
