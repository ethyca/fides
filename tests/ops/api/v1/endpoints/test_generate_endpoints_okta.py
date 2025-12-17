"""Tests for the generate API endpoint with Okta configuration."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from starlette.testclient import TestClient

from fides.api.api.v1.endpoints.generate import GenerateResponse, generate_okta
from fides.common.api.scope_registry import GENERATE_EXEC
from fides.connectors.models import ConnectorAuthFailureException, OktaConfig
from fideslang.models import Organization, System


class TestGenerateEndpointOkta:
    """Tests for the /generate/ endpoint with Okta target."""

    @pytest.mark.asyncio
    async def test_generate_okta_systems_success(
        self, test_client: TestClient, generate_auth_header, db
    ):
        """Test successful generation of Okta systems."""
        okta_config = {
            "orgUrl": "https://test.okta.com",
            "clientId": "test-client-id",
            "privateKey": '{"kty":"RSA","d":"test","n":"test","e":"AQAB"}',
        }

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

        with patch(
            "fides.api.api.v1.endpoints.generate.get_resource", new_callable=AsyncMock
        ) as mock_get_resource:
            with patch(
                "fides.api.api.v1.endpoints.generate.generate_okta"
            ) as mock_generate:
                mock_org = Mock(spec=Organization)
                mock_org.fides_key = "test-org"
                mock_get_resource.return_value = mock_org
                mock_generate.return_value = mock_systems

                response = test_client.post(
                    "/api/v1/generate/",
                    json={
                        "organization_key": "test-org",
                        "generate": {
                            "config": okta_config,
                            "target": "okta",
                            "type": "systems",
                        },
                    },
                    headers=generate_auth_header(scopes=[GENERATE_EXEC]),
                )

                assert response.status_code == status.HTTP_200_OK
                generate_response = GenerateResponse(**response.json())
                assert generate_response.generate_results is not None
                assert len(generate_response.generate_results) == 2

    @pytest.mark.asyncio
    async def test_generate_okta_auth_failure(
        self, test_client: TestClient, generate_auth_header, db
    ):
        """Test generation with authentication failure."""
        okta_config = {
            "orgUrl": "https://test.okta.com",
            "clientId": "invalid-client-id",
            "privateKey": '{"kty":"RSA","d":"test","n":"test","e":"AQAB"}',
        }

        with patch(
            "fides.api.api.v1.endpoints.generate.get_resource", new_callable=AsyncMock
        ) as mock_get_resource:
            with patch(
                "fides.api.api.v1.endpoints.generate.generate_okta"
            ) as mock_generate:
                mock_org = Mock(spec=Organization)
                mock_org.fides_key = "test-org"
                mock_get_resource.return_value = mock_org
                mock_generate.side_effect = ConnectorAuthFailureException(
                    "Authentication failed"
                )

                response = test_client.post(
                    "/api/v1/generate/",
                    json={
                        "organization_key": "test-org",
                        "generate": {
                            "config": okta_config,
                            "target": "okta",
                            "type": "systems",
                        },
                    },
                    headers=generate_auth_header(scopes=[GENERATE_EXEC]),
                )

                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert "Authentication failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_okta_wrong_config_type(
        self, test_client: TestClient, generate_auth_header, db
    ):
        """Test generation with wrong config type."""
        aws_config = {
            "region_name": "us-east-1",
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
        }

        with patch(
            "fides.api.api.v1.endpoints.generate.get_resource", new_callable=AsyncMock
        ) as mock_get_resource:
            mock_org = Mock(spec=Organization)
            mock_org.fides_key = "test-org"
            mock_get_resource.return_value = mock_org

            response = test_client.post(
                "/api/v1/generate/",
                json={
                    "organization_key": "test-org",
                    "generate": {
                        "config": aws_config,
                        "target": "okta",
                        "type": "systems",
                    },
                },
                headers=generate_auth_header(scopes=[GENERATE_EXEC]),
            )

            # Should return empty results when config type doesn't match
            assert response.status_code == status.HTTP_200_OK
            generate_response = GenerateResponse(**response.json())
            assert generate_response.generate_results is None


class TestGenerateOktaFunction:
    """Tests for the generate_okta function."""

    def test_generate_okta_success(self):
        """Test successful generation of Okta systems."""
        organization = Organization(fides_key="test-org")
        okta_config = OktaConfig(
            org_url="https://test.okta.com",
            client_id="test-client-id",
            private_key='{"kty":"RSA","d":"test","n":"test","e":"AQAB"}',
        )

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

        with patch(
            "fides.api.api.v1.endpoints.generate.validate_credentials"
        ) as mock_validate:
            with patch(
                "fides.api.api.v1.endpoints.generate.generate_okta_systems"
            ) as mock_generate_systems:
                mock_validate.return_value = None
                mock_generate_systems.return_value = mock_systems

                result = generate_okta(
                    okta_config=okta_config, organization=organization
                )

                assert len(result) == 2
                assert result[0]["fides_key"] == "app1"
                assert result[1]["fides_key"] == "app2"
                mock_validate.assert_called_once_with(okta_config)
                mock_generate_systems.assert_called_once_with(
                    organization=organization, okta_config=okta_config
                )

    def test_generate_okta_auth_failure(self):
        """Test generation with authentication failure."""
        organization = Organization(fides_key="test-org")
        okta_config = OktaConfig(
            org_url="https://test.okta.com",
            client_id="invalid-client-id",
            private_key='{"kty":"RSA","d":"test","n":"test","e":"AQAB"}',
        )

        with patch(
            "fides.api.api.v1.endpoints.generate.validate_credentials"
        ) as mock_validate:
            mock_validate.side_effect = ConnectorAuthFailureException(
                "Authentication failed"
            )

            with pytest.raises(HTTPException) as exc_info:
                generate_okta(okta_config=okta_config, organization=organization)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Authentication failed" in str(exc_info.value.detail)
            mock_validate.assert_called_once_with(okta_config)

    def test_generate_okta_empty_systems(self):
        """Test generation with empty systems list."""
        organization = Organization(fides_key="test-org")
        okta_config = OktaConfig(
            org_url="https://test.okta.com",
            client_id="test-client-id",
            private_key='{"kty":"RSA","d":"test","n":"test","e":"AQAB"}',
        )

        with patch(
            "fides.api.api.v1.endpoints.generate.validate_credentials"
        ) as mock_validate:
            with patch(
                "fides.api.api.v1.endpoints.generate.generate_okta_systems"
            ) as mock_generate_systems:
                mock_validate.return_value = None
                mock_generate_systems.return_value = []

                result = generate_okta(
                    okta_config=okta_config, organization=organization
                )

                assert result == []
                mock_validate.assert_called_once_with(okta_config)
                mock_generate_systems.assert_called_once_with(
                    organization=organization, okta_config=okta_config
                )
