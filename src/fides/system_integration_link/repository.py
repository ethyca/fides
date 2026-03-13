from typing import Any, Optional

from sqlalchemy import and_, delete, exists
from sqlalchemy.future import select
from sqlalchemy.orm import Load, Session, load_only, noload, selectinload

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.common.session_management import (
    with_optional_sync_readonly_session,
    with_optional_sync_session,
)
from fides.system_integration_link.entities import (
    ConnectionConfigRef,
    SystemIntegrationLinkEntity,
    SystemRef,
)
from fides.system_integration_link.models import (
    SystemConnectionConfigLink,
)


def linked_system_load_options() -> Load:
    """Eager-load only the System columns needed for LinkedSystemInfo,
    suppressing all of System's default selectin relationships to avoid
    a cascade of unnecessary queries."""
    return selectinload(ConnectionConfig.system).options(
        load_only(System.fides_key, System.name),
        noload("*"),
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
            select(SystemConnectionConfigLink, System.fides_key, System.name)
            .join(System, SystemConnectionConfigLink.system_id == System.id)
            .where(
                SystemConnectionConfigLink.connection_config_id == connection_config_id
            )
            .order_by(SystemConnectionConfigLink.created_at.asc())
        )
        rows = session.execute(stmt).all()
        return [
            SystemIntegrationLinkEntity.from_orm(
                link, system_fides_key=fides_key, system_name=name
            )
            for link, fides_key, name in rows
        ]

    @with_optional_sync_readonly_session
    def get_link(
        self,
        connection_config_id: str,
        system_id: str,
        *,
        session: Session,
    ) -> Optional[SystemIntegrationLinkEntity]:
        stmt = (
            select(SystemConnectionConfigLink, System.fides_key, System.name)
            .join(System, SystemConnectionConfigLink.system_id == System.id)
            .where(
                SystemConnectionConfigLink.connection_config_id == connection_config_id,
                SystemConnectionConfigLink.system_id == system_id,
            )
        )
        row = session.execute(stmt).first()
        if not row:
            return None
        link, fides_key, name = row
        return SystemIntegrationLinkEntity.from_orm(
            link, system_fides_key=fides_key, system_name=name
        )

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
        return self._to_entity_with_system(link, session=session)

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
            return self._to_entity_with_system(existing, session=session)

        link = SystemConnectionConfigLink(
            connection_config_id=connection_config_id,
            system_id=system_id,
        )
        session.add(link)
        session.flush()
        session.refresh(link)
        return self._to_entity_with_system(link, session=session)

    def _to_entity_with_system(
        self, link: SystemConnectionConfigLink, *, session: Session
    ) -> SystemIntegrationLinkEntity:
        """Convert an ORM link to an entity, fetching system info via a join."""
        stmt = select(System.fides_key, System.name).where(System.id == link.system_id)
        row = session.execute(stmt).one()
        return SystemIntegrationLinkEntity.from_orm(
            link,
            system_fides_key=row.fides_key,
            system_name=row.name,
        )

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
    ) -> Optional[ConnectionConfigRef]:
        stmt = select(ConnectionConfig.id, ConnectionConfig.key).where(
            ConnectionConfig.key == connection_key
        )
        row = session.execute(stmt).first()
        return ConnectionConfigRef(id=row.id, key=row.key) if row else None

    @with_optional_sync_readonly_session
    def resolve_system(
        self, system_fides_key: str, *, session: Session
    ) -> Optional[SystemRef]:
        stmt = select(System.id, System.fides_key).where(
            System.fides_key == system_fides_key
        )
        row = session.execute(stmt).first()
        return SystemRef(id=row.id, fides_key=row.fides_key) if row else None
