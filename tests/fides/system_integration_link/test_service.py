from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from fides.api import system_connection_config_link_change_hooks as link_hooks
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.sql_models import System
from fides.system_integration_link.entities import SystemLinkInput
from fides.system_integration_link.exceptions import (
    ConnectionConfigNotFoundError,
    SystemIntegrationLinkNotFoundError,
    SystemNotFoundError,
    TooManyLinksError,
)
from fides.system_integration_link.repository import SystemIntegrationLinkRepository
from fides.system_integration_link.service import (
    SystemIntegrationLinkService,
)


@pytest.fixture()
def service() -> SystemIntegrationLinkService:
    return SystemIntegrationLinkService()


@pytest.fixture()
def system_a(db: Session):
    system = System.create(
        db=db,
        data={
            "fides_key": "svc_test_system_a",
            "name": "Service Test System A",
            "organization_fides_key": "test_organization",
            "system_type": "Service",
        },
    )
    yield system
    system.delete(db)


@pytest.fixture()
def system_b(db: Session):
    system = System.create(
        db=db,
        data={
            "fides_key": "svc_test_system_b",
            "name": "Service Test System B",
            "organization_fides_key": "test_organization",
            "system_type": "Service",
        },
    )
    yield system
    system.delete(db)


@pytest.fixture()
def connection_config(db: Session):
    config = ConnectionConfig.create(
        db=db,
        data={
            "name": "Service Test Connection",
            "key": "svc_test_connection",
            "connection_type": "manual",
            "access": "read",
        },
    )
    yield config
    config.delete(db)


class TestGetLinksForConnection:
    def test_returns_links(self, service, db, connection_config, system_a):
        repo = SystemIntegrationLinkRepository()
        repo.create_or_update_link(
            system_id=system_a.id,
            connection_config_id=connection_config.id,
            session=db,
        )
        db.commit()

        result = service.get_links_for_connection(connection_config.key, session=db)

        assert len(result) == 1
        assert result[0].system_fides_key == "svc_test_system_a"
        assert result[0].connection_config_id == connection_config.id

    def test_returns_empty_list_when_no_links(self, service, db, connection_config):
        result = service.get_links_for_connection(connection_config.key, session=db)
        assert result == []

    def test_raises_when_connection_not_found(self, service, db):
        with pytest.raises(ConnectionConfigNotFoundError) as exc_info:
            service.get_links_for_connection("missing_conn", session=db)

        assert exc_info.value.connection_key == "missing_conn"


class TestSetLinks:
    def test_sets_single_link(self, service, db, connection_config, system_a):
        result = service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_a")],
            session=db,
        )
        db.commit()

        assert len(result) == 1
        assert result[0].system_fides_key == "svc_test_system_a"
        assert result[0].system_id == system_a.id
        assert result[0].connection_config_id == connection_config.id

    def test_set_link_overrides_existing(
        self, service, db, connection_config, system_a, system_b
    ):
        """Setting a new link should replace the existing one."""
        service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_a")],
            session=db,
        )
        db.commit()

        result = service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_b")],
            session=db,
        )
        db.commit()

        assert len(result) == 1
        assert result[0].system_fides_key == "svc_test_system_b"

        links = service.get_links_for_connection(connection_config.key, session=db)
        assert len(links) == 1
        assert links[0].system_fides_key == "svc_test_system_b"

    def test_clears_all_links_with_empty_list(
        self, service, db, connection_config, system_a
    ):
        service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_a")],
            session=db,
        )
        db.commit()

        result = service.set_links(connection_config.key, [], session=db)
        db.commit()

        assert result == []

        links = service.get_links_for_connection(connection_config.key, session=db)
        assert links == []

    def test_rejects_more_than_max_links(self, service, db, connection_config):
        with pytest.raises(TooManyLinksError) as exc_info:
            service.set_links(
                connection_config.key,
                [
                    SystemLinkInput(system_fides_key="sys_a"),
                    SystemLinkInput(system_fides_key="sys_b"),
                ],
                session=db,
            )

        assert exc_info.value.connection_key == connection_config.key
        assert exc_info.value.max_links == 1

    def test_raises_when_connection_not_found(self, service, db):
        with pytest.raises(ConnectionConfigNotFoundError):
            service.set_links(
                "missing_conn",
                [SystemLinkInput(system_fides_key="whatever")],
                session=db,
            )

    def test_raises_when_system_not_found(self, service, db, connection_config):
        with pytest.raises(SystemNotFoundError) as exc_info:
            service.set_links(
                connection_config.key,
                [SystemLinkInput(system_fides_key="ghost_system")],
                session=db,
            )

        assert exc_info.value.system_fides_key == "ghost_system"


class TestDeleteLink:
    def test_deletes_existing_link(self, service, db, connection_config, system_a):
        service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_a")],
            session=db,
        )
        db.commit()

        service.delete_link(connection_config.key, "svc_test_system_a", session=db)
        db.commit()

        links = service.get_links_for_connection(connection_config.key, session=db)
        assert links == []

    def test_raises_when_connection_not_found(self, service, db):
        with pytest.raises(ConnectionConfigNotFoundError):
            service.delete_link("missing", "whatever", session=db)

    def test_raises_when_system_not_found(self, service, db, connection_config):
        with pytest.raises(SystemNotFoundError):
            service.delete_link(connection_config.key, "ghost_system", session=db)

    def test_raises_when_link_not_found(self, service, db, connection_config, system_a):
        with pytest.raises(SystemIntegrationLinkNotFoundError) as exc_info:
            service.delete_link(connection_config.key, "svc_test_system_a", session=db)

        assert exc_info.value.connection_key == connection_config.key
        assert exc_info.value.system_fides_key == "svc_test_system_a"


class TestLinkChangeHookDispatch:
    """The mutator service methods must fire link-change hooks when
    ``background_tasks`` is provided and stay silent otherwise."""

    @pytest.fixture(autouse=True)
    def isolated_registry(self, monkeypatch):
        monkeypatch.setattr(link_hooks, "_HOOKS", [])
        yield

    def test_set_links_fires_hook_when_background_tasks_passed(
        self, service, db, connection_config, system_a
    ):
        hook = MagicMock()
        link_hooks.register_system_connection_config_link_change_hook(hook)
        bg = BackgroundTasks()

        service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_a")],
            session=db,
            background_tasks=bg,
        )

        hook.assert_called_once_with(bg, connection_config.id)

    def test_set_links_silent_when_no_background_tasks(
        self, service, db, connection_config, system_a
    ):
        hook = MagicMock()
        link_hooks.register_system_connection_config_link_change_hook(hook)

        service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_a")],
            session=db,
        )

        hook.assert_not_called()

    def test_set_links_does_not_fire_on_empty_set_with_no_prior_links(
        self, service, db, connection_config
    ):
        """Calling ``set_links([])`` on a connection that had no links is a
        true no-op — no DB state changed, so the hook must not fire even
        though ``background_tasks`` was supplied."""
        hook = MagicMock()
        link_hooks.register_system_connection_config_link_change_hook(hook)
        bg = BackgroundTasks()

        service.set_links(connection_config.key, [], session=db, background_tasks=bg)

        hook.assert_not_called()

    def test_delete_link_fires_hook_when_background_tasks_passed(
        self, service, db, connection_config, system_a
    ):
        service.set_links(
            connection_config.key,
            [SystemLinkInput(system_fides_key="svc_test_system_a")],
            session=db,
        )
        db.commit()

        hook = MagicMock()
        link_hooks.register_system_connection_config_link_change_hook(hook)
        bg = BackgroundTasks()

        service.delete_link(
            connection_config.key,
            "svc_test_system_a",
            session=db,
            background_tasks=bg,
        )

        hook.assert_called_once_with(bg, connection_config.id)

    def test_delete_link_does_not_fire_when_link_missing(
        self, service, db, connection_config, system_a
    ):
        """If ``delete_link`` raises ``SystemIntegrationLinkNotFoundError``
        the hook must not fire — nothing actually changed."""
        hook = MagicMock()
        link_hooks.register_system_connection_config_link_change_hook(hook)
        bg = BackgroundTasks()

        with pytest.raises(SystemIntegrationLinkNotFoundError):
            service.delete_link(
                connection_config.key,
                "svc_test_system_a",
                session=db,
                background_tasks=bg,
            )

        hook.assert_not_called()
