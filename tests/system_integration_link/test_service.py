from datetime import datetime, timezone
from unittest.mock import MagicMock, create_autospec

import pytest

from fides.system_integration_link.entities import (
    SystemIntegrationLinkEntity,
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
from fides.system_integration_link.service import (
    SystemIntegrationLinkService,
)

NOW = datetime(2026, 2, 18, 12, 0, 0, tzinfo=timezone.utc)


def _make_entity(
    system_fides_key: str = "test_system",
    system_id: str = "sys-id-1",
    connection_config_id: str = "cc-id-1",
) -> SystemIntegrationLinkEntity:
    return SystemIntegrationLinkEntity(
        id="link-id-1",
        system_id=system_id,
        connection_config_id=connection_config_id,
        created_at=NOW,
        updated_at=NOW,
        system_fides_key=system_fides_key,
        system_name=f"{system_fides_key} name",
    )


def _make_connection_config(key: str = "my_connection", id_: str = "cc-id-1"):
    cc = MagicMock()
    cc.key = key
    cc.id = id_
    return cc


def _make_system(fides_key: str = "test_system", id_: str = "sys-id-1"):
    sys = MagicMock()
    sys.fides_key = fides_key
    sys.id = id_
    return sys


@pytest.fixture()
def mock_repo():
    return create_autospec(SystemIntegrationLinkRepository, instance=True)


@pytest.fixture()
def service(mock_repo):
    return SystemIntegrationLinkService(repo=mock_repo)


@pytest.fixture()
def mock_session():
    return MagicMock()


class TestGetLinksForConnection:
    def test_returns_links(self, service, mock_repo, mock_session):
        entity = _make_entity()
        mock_repo.resolve_connection_config.return_value = _make_connection_config()
        mock_repo.get_links_for_connection.return_value = [entity]

        result = service.get_links_for_connection("my_connection", session=mock_session)

        assert result == [entity]
        mock_repo.resolve_connection_config.assert_called_once_with(
            "my_connection", session=mock_session
        )

    def test_returns_empty_list_when_no_links(self, service, mock_repo, mock_session):
        mock_repo.resolve_connection_config.return_value = _make_connection_config()
        mock_repo.get_links_for_connection.return_value = []

        result = service.get_links_for_connection("my_connection", session=mock_session)

        assert result == []

    def test_raises_when_connection_not_found(self, service, mock_repo, mock_session):
        mock_repo.resolve_connection_config.return_value = None

        with pytest.raises(ConnectionConfigNotFoundError) as exc_info:
            service.get_links_for_connection("missing_conn", session=mock_session)

        assert exc_info.value.connection_key == "missing_conn"


class TestSetLinks:
    def test_sets_single_link(self, service, mock_repo, mock_session):
        cc = _make_connection_config()
        sys = _make_system()
        entity = _make_entity()
        mock_repo.resolve_connection_config.return_value = cc
        mock_repo.resolve_system.return_value = sys
        mock_repo.delete_all_links_for_connection.return_value = 0
        mock_repo.get_or_create_link.return_value = entity

        result = service.set_links(
            "my_connection",
            [{"system_fides_key": "test_system"}],
            session=mock_session,
        )

        assert result == [entity]
        mock_repo.delete_all_links_for_connection.assert_called_once_with(
            cc.id, session=mock_session
        )
        mock_repo.get_or_create_link.assert_called_once_with(
            connection_config_id=cc.id,
            system_id=sys.id,
            session=mock_session,
        )

    def test_idempotent_replace_with_preexisting_links(
        self, service, mock_repo, mock_session
    ):
        """set_links with 1 link should succeed even when
        there are already links in the DB (old code counted existing + new)."""
        cc = _make_connection_config()
        sys = _make_system(fides_key="new_system", id_="sys-id-2")
        new_entity = _make_entity(system_fides_key="new_system", system_id="sys-id-2")
        mock_repo.resolve_connection_config.return_value = cc
        mock_repo.resolve_system.return_value = sys
        mock_repo.delete_all_links_for_connection.return_value = 2
        mock_repo.get_or_create_link.return_value = new_entity

        result = service.set_links(
            "my_connection",
            [{"system_fides_key": "new_system"}],
            session=mock_session,
        )

        assert result == [new_entity]
        mock_repo.delete_all_links_for_connection.assert_called_once()

    def test_clears_all_links_with_empty_list(self, service, mock_repo, mock_session):
        cc = _make_connection_config()
        mock_repo.resolve_connection_config.return_value = cc
        mock_repo.delete_all_links_for_connection.return_value = 1

        result = service.set_links("my_connection", [], session=mock_session)

        assert result == []
        mock_repo.delete_all_links_for_connection.assert_called_once_with(
            cc.id, session=mock_session
        )
        mock_repo.get_or_create_link.assert_not_called()

    def test_rejects_more_than_max_links(self, service, mock_repo, mock_session):
        with pytest.raises(TooManyLinksError) as exc_info:
            service.set_links(
                "my_connection",
                [
                    {"system_fides_key": "sys_a"},
                    {"system_fides_key": "sys_b"},
                ],
                session=mock_session,
            )

        assert exc_info.value.connection_key == "my_connection"
        assert exc_info.value.max_links == 1
        mock_repo.resolve_connection_config.assert_not_called()

    def test_raises_when_connection_not_found(self, service, mock_repo, mock_session):
        mock_repo.resolve_connection_config.return_value = None

        with pytest.raises(ConnectionConfigNotFoundError):
            service.set_links(
                "missing_conn",
                [{"system_fides_key": "test_system"}],
                session=mock_session,
            )

    def test_raises_when_system_not_found(self, service, mock_repo, mock_session):
        mock_repo.resolve_connection_config.return_value = _make_connection_config()
        mock_repo.resolve_system.return_value = None

        with pytest.raises(SystemNotFoundError) as exc_info:
            service.set_links(
                "my_connection",
                [{"system_fides_key": "ghost_system"}],
                session=mock_session,
            )

        assert exc_info.value.system_fides_key == "ghost_system"


class TestDeleteLink:
    def test_deletes_existing_link(self, service, mock_repo, mock_session):
        cc = _make_connection_config()
        sys = _make_system()
        mock_repo.resolve_connection_config.return_value = cc
        mock_repo.resolve_system.return_value = sys
        mock_repo.delete_links.return_value = 1

        service.delete_link("my_connection", "test_system", session=mock_session)

        mock_repo.delete_links.assert_called_once_with(
            connection_config_id=cc.id,
            system_id=sys.id,
            session=mock_session,
        )

    def test_raises_when_connection_not_found(self, service, mock_repo, mock_session):
        mock_repo.resolve_connection_config.return_value = None

        with pytest.raises(ConnectionConfigNotFoundError):
            service.delete_link("missing", "test_system", session=mock_session)

    def test_raises_when_system_not_found(self, service, mock_repo, mock_session):
        mock_repo.resolve_connection_config.return_value = _make_connection_config()
        mock_repo.resolve_system.return_value = None

        with pytest.raises(SystemNotFoundError):
            service.delete_link("my_connection", "ghost", session=mock_session)

    def test_raises_when_link_not_found(self, service, mock_repo, mock_session):
        mock_repo.resolve_connection_config.return_value = _make_connection_config()
        mock_repo.resolve_system.return_value = _make_system()
        mock_repo.delete_links.return_value = 0

        with pytest.raises(SystemIntegrationLinkNotFoundError) as exc_info:
            service.delete_link("my_connection", "test_system", session=mock_session)

        assert exc_info.value.connection_key == "my_connection"
        assert exc_info.value.system_fides_key == "test_system"
