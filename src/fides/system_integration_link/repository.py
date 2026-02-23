from typing import Optional

from sqlalchemy.orm import Session, joinedload

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.core.repository.session_management import with_optional_sync_session
from fides.system_integration_link.entities import (
    SystemIntegrationLinkEntity,
)
from fides.system_integration_link.models import (
    SystemConnectionConfigLink,
)


class SystemIntegrationLinkRepository:
    """Data access layer for system-integration links."""

    @with_optional_sync_session
    def get_links_for_connection(
        self, connection_config_id: str, *, session: Session
    ) -> list[SystemIntegrationLinkEntity]:
        links = (
            session.query(SystemConnectionConfigLink)
            .options(joinedload(SystemConnectionConfigLink.system))
            .filter(
                SystemConnectionConfigLink.connection_config_id == connection_config_id
            )
            .order_by(SystemConnectionConfigLink.created_at.asc())
            .all()
        )
        return [SystemIntegrationLinkEntity.from_orm(link) for link in links]

    @with_optional_sync_session
    def get_link(
        self,
        connection_config_id: str,
        system_id: str,
        *,
        session: Session,
    ) -> Optional[SystemIntegrationLinkEntity]:
        link = (
            session.query(SystemConnectionConfigLink)
            .options(joinedload(SystemConnectionConfigLink.system))
            .filter(
                SystemConnectionConfigLink.connection_config_id == connection_config_id,
                SystemConnectionConfigLink.system_id == system_id,
            )
            .first()
        )
        return SystemIntegrationLinkEntity.from_orm(link) if link else None

    @with_optional_sync_session
    def upsert_link(
        self,
        connection_config_id: str,
        system_id: str,
        *,
        session: Session,
    ) -> SystemIntegrationLinkEntity:
        """Create or return an existing link for the given pair."""
        existing = (
            session.query(SystemConnectionConfigLink)
            .filter(
                SystemConnectionConfigLink.connection_config_id == connection_config_id,
                SystemConnectionConfigLink.system_id == system_id,
            )
            .first()
        )
        if existing:
            session.refresh(existing)
            return SystemIntegrationLinkEntity.from_orm(existing)

        link = SystemConnectionConfigLink(
            connection_config_id=connection_config_id,
            system_id=system_id,
        )
        session.add(link)
        session.flush()
        session.refresh(link)
        return SystemIntegrationLinkEntity.from_orm(link)

    @with_optional_sync_session
    def delete_links(
        self,
        connection_config_id: str,
        system_id: str,
        *,
        session: Session,
    ) -> int:
        """Delete the link for a specific system. Returns the number of rows deleted."""
        count = (
            session.query(SystemConnectionConfigLink)
            .filter(
                SystemConnectionConfigLink.connection_config_id == connection_config_id,
                SystemConnectionConfigLink.system_id == system_id,
            )
            .delete(synchronize_session="evaluate")
        )
        session.flush()
        return count

    @with_optional_sync_session
    def delete_all_links_for_connection(
        self,
        connection_config_id: str,
        *,
        session: Session,
    ) -> int:
        """Delete all links for a connection config. Returns the number of rows deleted."""
        count = (
            session.query(SystemConnectionConfigLink)
            .filter(
                SystemConnectionConfigLink.connection_config_id == connection_config_id,
            )
            .delete(synchronize_session="evaluate")
        )
        session.flush()
        return count

    @with_optional_sync_session
    def resolve_connection_config(
        self, connection_key: str, *, session: Session
    ) -> Optional[ConnectionConfig]:
        return (
            session.query(ConnectionConfig)
            .filter(ConnectionConfig.key == connection_key)
            .first()
        )

    @with_optional_sync_session
    def resolve_system(
        self, system_fides_key: str, *, session: Session
    ) -> Optional[System]:
        return (
            session.query(System).filter(System.fides_key == system_fides_key).first()
        )
