from typing import Any, Optional

from sqlalchemy import and_, delete, exists
from sqlalchemy.future import select
from sqlalchemy.orm import Session, joinedload

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.core.repository.session_management import (
    with_optional_sync_readonly_session,
    with_optional_sync_session,
)
from fides.system_integration_link.entities import (
    SystemIntegrationLinkEntity,
)
from fides.system_integration_link.models import (
    SystemConnectionConfigLink,
)


class SystemIntegrationLinkRepository:
    """Data access layer for system-integration links."""

    @staticmethod
    def has_system_link_exists_clause() -> Any:
        """Correlated EXISTS clause for filtering ConnectionConfigs that have a link.

        Usage::

            has_link = SystemIntegrationLinkRepository.has_system_link_exists_clause()
            query.filter(has_link)      # linked only
            query.filter(~has_link)     # orphaned only
        """
        return exists(
            select(SystemConnectionConfigLink.id).where(
                SystemConnectionConfigLink.connection_config_id == ConnectionConfig.id
            )
        )

    @with_optional_sync_readonly_session
    def get_links_for_connection(
        self, connection_config_id: str, *, session: Session
    ) -> list[SystemIntegrationLinkEntity]:
        stmt = (
            select(SystemConnectionConfigLink)
            .options(joinedload(SystemConnectionConfigLink.system))
            .where(
                SystemConnectionConfigLink.connection_config_id == connection_config_id
            )
            .order_by(SystemConnectionConfigLink.created_at.asc())
        )
        links = session.execute(stmt).scalars().unique().all()
        return [SystemIntegrationLinkEntity.from_orm(link) for link in links]

    @with_optional_sync_readonly_session
    def get_link(
        self,
        connection_config_id: str,
        system_id: str,
        *,
        session: Session,
    ) -> Optional[SystemIntegrationLinkEntity]:
        stmt = (
            select(SystemConnectionConfigLink)
            .options(joinedload(SystemConnectionConfigLink.system))
            .where(
                SystemConnectionConfigLink.connection_config_id == connection_config_id,
                SystemConnectionConfigLink.system_id == system_id,
            )
        )
        link = session.execute(stmt).scalars().unique().first()
        return SystemIntegrationLinkEntity.from_orm(link) if link else None

    @with_optional_sync_session
    def create_or_update_link(
        self,
        system_id: str,
        connection_config_id: str,
        *,
        session: Session,
    ) -> SystemIntegrationLinkEntity:
        """Replace any existing link for this connection_config with a new one.

        Ensures at most one system link per connection config.  The delete
        intentionally filters only by connection_config_id (not system_id)
        so that re-pointing a CC to a different system removes the old link.
        If the unique constraint on connection_config_id is ever relaxed for
        many-to-many, this method must be revisited.
        """
        session.execute(
            delete(SystemConnectionConfigLink.__table__).where(
                SystemConnectionConfigLink.connection_config_id == connection_config_id
            )
        )

        link = SystemConnectionConfigLink(
            system_id=system_id,
            connection_config_id=connection_config_id,
        )
        session.add(link)
        session.flush()
        session.refresh(link)
        return SystemIntegrationLinkEntity.from_orm(link)

    @with_optional_sync_session
    def get_or_create_link(
        self,
        connection_config_id: str,
        system_id: str,
        *,
        session: Session,
    ) -> SystemIntegrationLinkEntity:
        """Create or return an existing link for the given pair."""
        stmt = select(SystemConnectionConfigLink).where(
            SystemConnectionConfigLink.connection_config_id == connection_config_id,
            SystemConnectionConfigLink.system_id == system_id,
        )
        existing = session.execute(stmt).scalars().first()
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
        result = session.execute(
            delete(SystemConnectionConfigLink.__table__).where(
                and_(
                    SystemConnectionConfigLink.connection_config_id
                    == connection_config_id,
                    SystemConnectionConfigLink.system_id == system_id,
                )
            )
        )
        session.flush()
        return result.rowcount  # type: ignore[union-attr]

    @with_optional_sync_session
    def delete_all_links_for_connection(
        self,
        connection_config_id: str,
        *,
        session: Session,
    ) -> int:
        """Delete all links for a connection config. Returns the number of rows deleted."""
        result = session.execute(
            delete(SystemConnectionConfigLink.__table__).where(
                SystemConnectionConfigLink.connection_config_id == connection_config_id,
            )
        )
        session.flush()
        return result.rowcount  # type: ignore[union-attr]

    @with_optional_sync_readonly_session
    def resolve_connection_config(
        self, connection_key: str, *, session: Session
    ) -> Optional[ConnectionConfig]:
        stmt = select(ConnectionConfig).where(ConnectionConfig.key == connection_key)
        return session.execute(stmt).scalars().first()

    @with_optional_sync_readonly_session
    def resolve_system(
        self, system_fides_key: str, *, session: Session
    ) -> Optional[System]:
        stmt = select(System).where(System.fides_key == system_fides_key)
        return session.execute(stmt).scalars().first()
