from __future__ import annotations

import pytest
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.models.consent_settings import ConsentSettings
from fides.common.api.scope_registry import (
    CONSENT_SETTINGS_READ,
    CONSENT_SETTINGS_UPDATE,
)
from fides.common.api.v1 import urn_registry as urls


class TestGetConsentSettings:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONSENT_SETTINGS

    def test_get_consent_settings_unauthenticated(self, api_client: TestClient, url):
        response = api_client.get(url, headers={})
        assert 200 == response.status_code

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_200_OK),
            ("viewer", HTTP_200_OK),
            ("approver", HTTP_200_OK),
        ],
    )
    def test_get_consent_settings_with_roles(
        self,
        role,
        expected_status,
        api_client: TestClient,
        url,
        generate_role_header,
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == expected_status

    def test_get_consent_settings(
        self, api_client: TestClient, url, generate_auth_header
    ) -> None:
        auth_header = generate_auth_header([CONSENT_SETTINGS_READ])
        response = api_client.get(url, headers=auth_header)
        assert response.status_code == 200
        assert response.json()["tcf_enabled"] is False


class TestPatchConsentSettings:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONSENT_SETTINGS

    def test_patch_consent_settings_unauthenticated(self, api_client: TestClient, url):
        response = api_client.patch(url, headers={}, json={"tcf_enabled": True})
        assert 401 == response.status_code

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            ("owner", HTTP_200_OK),
            ("contributor", HTTP_200_OK),
            ("viewer_and_approver", HTTP_403_FORBIDDEN),
            ("viewer", HTTP_403_FORBIDDEN),
            ("approver", HTTP_403_FORBIDDEN),
        ],
    )
    def test_patch_consent_settings_with_roles(
        self,
        role,
        expected_status,
        api_client: TestClient,
        url,
        generate_role_header,
    ) -> None:
        auth_header = generate_role_header(roles=[role])
        response = api_client.patch(url, headers=auth_header, json={})
        assert response.status_code == expected_status

    def test_patch_consent_settings(
        self, db, api_client: TestClient, url, generate_auth_header
    ) -> None:
        consent_settings = ConsentSettings.get_or_create_with_defaults(db)
        consent_settings.update(db=db, data={"tcf_enabled": False})
        auth_header = generate_auth_header([CONSENT_SETTINGS_UPDATE])
        response = api_client.patch(
            url, headers=auth_header, json={"tcf_enabled": True}
        )
        assert response.status_code == 200
        assert response.json()["tcf_enabled"] is True
