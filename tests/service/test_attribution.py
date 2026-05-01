"""Unit tests for fides.service.attribution.AttributionService."""

from unittest.mock import MagicMock, patch

import pytest

from fides.service.attribution import AttributionService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return AttributionService(mock_db)


class TestGetActorDisplayName:
    def test_returns_none_when_both_ids_none(self, service):
        assert service.get_actor_display_name(user_id=None, client_id=None) is None

    def test_returns_fallback_when_both_ids_none(self, service):
        result = service.get_actor_display_name(
            user_id=None, client_id=None, fallback="unknown"
        )
        assert result == "unknown"

    def test_returns_root_username_for_root_client_id(self, service):
        with patch("fides.service.attribution.CONFIG") as mock_config:
            mock_config.security.oauth_root_client_id = "root_client_id"
            mock_config.security.root_username = "root"
            result = service.get_actor_display_name(
                user_id="root_client_id", client_id=None
            )
        assert result == "root"

    def test_returns_username_for_known_user(self, service):
        mock_user = MagicMock()
        mock_user.username = "alice"
        with (
            patch("fides.service.attribution.CONFIG") as mock_config,
            patch("fides.service.attribution.FidesUser.get_by", return_value=mock_user),
        ):
            mock_config.security.oauth_root_client_id = "root_client_id"
            result = service.get_actor_display_name(user_id="usr_123", client_id=None)
        assert result == "alice"

    def test_returns_fallback_when_user_not_found(self, service):
        with (
            patch("fides.service.attribution.CONFIG") as mock_config,
            patch("fides.service.attribution.FidesUser.get_by", return_value=None),
        ):
            mock_config.security.oauth_root_client_id = "root_client_id"
            result = service.get_actor_display_name(
                user_id="usr_deleted", client_id=None, fallback="usr_deleted"
            )
        assert result == "usr_deleted"

    def test_returns_client_name_for_named_client(self, service, mock_db):
        mock_client = MagicMock()
        mock_client.name = "My API Client"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        with patch("fides.service.attribution.CONFIG") as mock_config:
            mock_config.security.oauth_root_client_id = "root_client_id"
            result = service.get_actor_display_name(user_id=None, client_id="cli_abc")
        assert result == "My API Client"

    def test_returns_client_id_when_client_has_no_name(self, service, mock_db):
        mock_client = MagicMock()
        mock_client.name = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        with patch("fides.service.attribution.CONFIG") as mock_config:
            mock_config.security.oauth_root_client_id = "root_client_id"
            result = service.get_actor_display_name(user_id=None, client_id="cli_abc")
        assert result == "cli_abc"

    def test_returns_client_id_when_client_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch("fides.service.attribution.CONFIG") as mock_config:
            mock_config.security.oauth_root_client_id = "root_client_id"
            result = service.get_actor_display_name(
                user_id=None, client_id="cli_missing"
            )
        assert result == "cli_missing"

    def test_user_id_takes_precedence_when_both_set(self, service, mock_db):
        """user_id should be used if both are somehow set (should not happen in practice)."""
        mock_user = MagicMock()
        mock_user.username = "alice"
        with (
            patch("fides.service.attribution.CONFIG") as mock_config,
            patch("fides.service.attribution.FidesUser.get_by", return_value=mock_user),
        ):
            mock_config.security.oauth_root_client_id = "root_client_id"
            result = service.get_actor_display_name(
                user_id="usr_123", client_id="cli_abc"
            )
        assert result == "alice"
        # client lookup should not be called
        mock_db.query.assert_not_called()
