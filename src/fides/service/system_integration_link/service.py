from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.core.repository.session_management import with_optional_sync_session
from fides.service.system_integration_link.entities import (
    SystemIntegrationLinkEntity,
)
from fides.service.system_integration_link.exceptions import (
    ConnectionConfigNotFoundError,
    SystemIntegrationLinkNotFoundError,
    SystemNotFoundError,
    TooManyLinksError,
)
from fides.service.system_integration_link.models import SystemConnectionLinkType
from fides.service.system_integration_link.repository import (
    SystemIntegrationLinkRepository,
)

MAX_LINKS_PER_CONNECTION = 1


class SystemIntegrationLinkService:
    """Business logic for managing system-integration links."""

    def __init__(self, repo: Optional[SystemIntegrationLinkRepository] = None) -> None:
        self._repo = repo or SystemIntegrationLinkRepository()

    @with_optional_sync_session
    def get_links_for_connection(
        self, connection_key: str, *, session: Session
    ) -> list[SystemIntegrationLinkEntity]:
        connection_config = self._repo.resolve_connection_config(
            connection_key, session=session
        )
        if not connection_config:
            raise ConnectionConfigNotFoundError(connection_key)
        return self._repo.get_links_for_connection(
            connection_config.id, session=session
        )

    @with_optional_sync_session
    def set_links(
        self,
        connection_key: str,
        links: list[dict],
        *,
        session: Session,
    ) -> list[SystemIntegrationLinkEntity]:
        """Idempotent replace: the provided list becomes the complete set of links
        for this connection. Any existing links not in the new set are removed.

        Currently limited to MAX_LINKS_PER_CONNECTION total links per integration.
        """
        if len(links) > MAX_LINKS_PER_CONNECTION:
            raise TooManyLinksError(connection_key, MAX_LINKS_PER_CONNECTION)

        connection_config = self._repo.resolve_connection_config(
            connection_key, session=session
        )
        if not connection_config:
            raise ConnectionConfigNotFoundError(connection_key)

        for link_spec in links:
            system = self._repo.resolve_system(
                link_spec["system_fides_key"], session=session
            )
            if not system:
                raise SystemNotFoundError(link_spec["system_fides_key"])

        self._repo.delete_all_links_for_connection(
            connection_config.id, session=session
        )

        results: list[SystemIntegrationLinkEntity] = []
        for link_spec in links:
            system = self._repo.resolve_system(
                link_spec["system_fides_key"], session=session
            )
            entity = self._repo.upsert_link(
                connection_config_id=connection_config.id,
                system_id=system.id,
                link_type=SystemConnectionLinkType(link_spec["link_type"]),
                session=session,
            )
            results.append(entity)

        logger.info(
            "Set {} system link(s) for connection '{}'",
            len(results),
            connection_key,
        )
        return results

    @with_optional_sync_session
    def delete_link(
        self,
        connection_key: str,
        system_fides_key: str,
        link_type: Optional[SystemConnectionLinkType] = None,
        *,
        session: Session,
    ) -> None:
        connection_config = self._repo.resolve_connection_config(
            connection_key, session=session
        )
        if not connection_config:
            raise ConnectionConfigNotFoundError(connection_key)

        system = self._repo.resolve_system(system_fides_key, session=session)
        if not system:
            raise SystemNotFoundError(system_fides_key)

        count = self._repo.delete_links(
            connection_config_id=connection_config.id,
            system_id=system.id,
            link_type=link_type,
            session=session,
        )
        if count == 0:
            raise SystemIntegrationLinkNotFoundError(connection_key, system_fides_key)

        logger.info(
            "Deleted {} link(s) between connection '{}' and system '{}'",
            count,
            connection_key,
            system_fides_key,
        )
