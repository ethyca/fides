"""Tests for Okta system generation functions in fides.core.system."""

from unittest.mock import Mock, patch

from fideslang.models import Organization, System

from fides.connectors.models import OktaConfig
from fides.core import system as _system


class TestGenerateOktaSystems:
    """Tests for generate_okta_systems function."""

    def test_generate_okta_systems_success(self):
        """Test successful generation of Okta systems."""
        organization = Organization(fides_key="test-org")
        okta_config = OktaConfig(
            org_url="https://test.okta.com",
            client_id="test-client-id",
            private_key='{"kty":"RSA","d":"test","n":"test","e":"AQAB"}',
        )

        mock_applications = [
            {"id": "app1", "name": "App 1", "status": "ACTIVE"},
            {"id": "app2", "name": "App 2", "status": "ACTIVE"},
        ]

        mock_systems = [
            System(
                fides_key="app1",
                name="App 1",
                system_type="okta_application",
                privacy_declarations=[],
            ),
            System(
                fides_key="app2",
                name="App 2",
                system_type="okta_application",
                privacy_declarations=[],
            ),
        ]

        with patch("fides.connectors.okta.get_okta_client") as mock_get_client:
            with patch(
                "fides.connectors.okta.list_okta_applications"
            ) as mock_list_apps:
                with patch("fides.connectors.okta.create_okta_systems") as mock_create:
                    mock_client = Mock()
                    mock_get_client.return_value = mock_client
                    mock_list_apps.return_value = mock_applications
                    mock_create.return_value = mock_systems

                    result = _system.generate_okta_systems(
                        organization=organization, okta_config=okta_config
                    )

                    assert result == mock_systems
                    mock_get_client.assert_called_once_with(okta_config)
                    mock_list_apps.assert_called_once_with(okta_client=mock_client)
                    mock_create.assert_called_once_with(
                        okta_applications=mock_applications,
                        organization_key="test-org",
                    )

    def test_generate_okta_systems_with_none_config(self):
        """Test generation with None config."""
        organization = Organization(fides_key="test-org")

        with patch("fides.connectors.okta.get_okta_client") as mock_get_client:
            with patch(
                "fides.connectors.okta.list_okta_applications"
            ) as mock_list_apps:
                with patch("fides.connectors.okta.create_okta_systems") as mock_create:
                    mock_client = Mock()
                    mock_get_client.return_value = mock_client
                    mock_list_apps.return_value = []
                    mock_create.return_value = []

                    result = _system.generate_okta_systems(
                        organization=organization, okta_config=None
                    )

                    assert result == []
                    mock_get_client.assert_called_once_with(None)
                    mock_list_apps.assert_called_once_with(okta_client=mock_client)
                    mock_create.assert_called_once_with(
                        okta_applications=[], organization_key="test-org"
                    )

    def test_generate_okta_systems_empty_applications(self):
        """Test generation with empty applications list."""
        organization = Organization(fides_key="test-org")
        okta_config = OktaConfig(
            org_url="https://test.okta.com",
            client_id="test-client-id",
            private_key='{"kty":"RSA","d":"test","n":"test","e":"AQAB"}',
        )

        with patch("fides.connectors.okta.get_okta_client") as mock_get_client:
            with patch(
                "fides.connectors.okta.list_okta_applications"
            ) as mock_list_apps:
                with patch("fides.connectors.okta.create_okta_systems") as mock_create:
                    mock_client = Mock()
                    mock_get_client.return_value = mock_client
                    mock_list_apps.return_value = []
                    mock_create.return_value = []

                    result = _system.generate_okta_systems(
                        organization=organization, okta_config=okta_config
                    )

                    assert result == []
                    mock_get_client.assert_called_once_with(okta_config)
                    mock_list_apps.assert_called_once_with(okta_client=mock_client)
                    mock_create.assert_called_once_with(
                        okta_applications=[], organization_key="test-org"
                    )
