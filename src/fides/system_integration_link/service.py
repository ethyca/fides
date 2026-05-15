from typing import Optional

from fastapi import BackgroundTasks
from loguru import logger
from sqlalchemy.orm import Session

from fides.api.system_connection_config_link_change_hooks import (
    notify_system_connection_config_link_changed,
)
from fides.common.session_management import (
    with_optional_sync_readonly_session,
    with_optional_sync_session,
)
from fides.system_integration_link.entities import (
    SystemIntegrationLinkEntity,
    SystemLinkInput,
    SystemRef,
)
from fides.system_integration_link.exceptions import (
    ConnectionConfigNotFoundError,
    SystemIntegrationLinkNotFoundError,
    SystemNotFoundError,
    TooManyLinksError,
)
from fides.system_integration_link.repository import (
    SystemIntegrationLinkRepository,
)

MAX_LINKS_PER_CONNECTION = 1


class SystemIntegrationLinkService:
    """Business logic for managing system-integration links."""

    def __init__(self, repo: Optional[SystemIntegrationLinkRepository] = None) -> None:
        self._repo = repo or SystemIntegrationLinkRepository()

    @with_optional_sync_readonly_session
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
        links: list[SystemLinkInput],
        *,
        session: Session,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> list[SystemIntegrationLinkEntity]:
        """Idempotent replace: the provided list becomes the complete set of links
        for this connection. Any existing links not in the new set are removed.

        Currently limited to MAX_LINKS_PER_CONNECTION total links per integration.

        When ``background_tasks`` is provided and the call actually mutated
        rows (i.e. there were prior links or new links to set), fires the
        system-connection-config-link-change hooks so consumers (e.g.
        fidesplus's inheritance propagation) can react. The no-op case —
        ``set_links([])`` when no links previously existed — does not fire.
        Note: re-setting an identical link is treated as a mutation (the
        implementation does delete-and-recreate), so the hook fires even
        though the logical set is unchanged; tolerable because consumers
        are expected to be idempotent.
        """
        connection_config = self._repo.resolve_connection_config(
            connection_key, session=session
        )
        if not connection_config:
            raise ConnectionConfigNotFoundError(connection_key)

        if len(links) > MAX_LINKS_PER_CONNECTION:
            raise TooManyLinksError(connection_key, MAX_LINKS_PER_CONNECTION)

        system_map: dict[str, SystemRef] = {}
        for link_spec in links:
            system = self._repo.resolve_system(
                link_spec.system_fides_key, session=session
            )
            if not system:
                raise SystemNotFoundError(link_spec.system_fides_key)
            system_map[link_spec.system_fides_key] = system

        had_existing_links = bool(
            self._repo.get_links_for_connection(connection_config.id, session=session)
        )

        self._repo.delete_all_links_for_connection(
            connection_config.id, session=session
        )

        results: list[SystemIntegrationLinkEntity] = []
        for link_spec in links:
            system = system_map[link_spec.system_fides_key]
            entity = self._repo.get_or_create_link(
                connection_config_id=connection_config.id,
                system_id=system.id,
                session=session,
            )
            results.append(entity)

        logger.info(
            "Set {} system link(s) for connection '{}'",
            len(results),
            connection_key,
        )

        if background_tasks is not None and (had_existing_links or results):
            notify_system_connection_config_link_changed(
                background_tasks, connection_config.id
            )
        return results

    @with_optional_sync_session
    def delete_link(
        self,
        connection_key: str,
        system_fides_key: str,
        *,
        session: Session,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> None:
        """Delete a single system↔connection-config link.

        When ``background_tasks`` is provided and the link existed (i.e. the
        delete actually removed a row), fires the link-change hooks.
        """
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
            session=session,
        )
        if count == 0:
            raise SystemIntegrationLinkNotFoundError(connection_key, system_fides_key)

        logger.info(
            "Deleted link between connection '{}' and system '{}'",
            connection_key,
            system_fides_key,
        )

        if background_tasks is not None:
            notify_system_connection_config_link_changed(
                background_tasks, connection_config.id
            )
