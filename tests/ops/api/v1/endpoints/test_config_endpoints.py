import pytest
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from fides.api.ops.api.v1 import scope_registry as scopes
from fides.api.ops.api.v1 import urn_registry as urls
from fides.api.ops.models.application_config import ApplicationConfig

ACTIVE_DEFAULT_STORAGE_KEY = "fides.storage.active_default_storage_type"


class TestPatchApplicationConfig:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {ACTIVE_DEFAULT_STORAGE_KEY: "s3"}

    def test_patch_application_config_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.patch(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_patch_application_config_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_patch_application_config_with_invalid_key(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(url, headers=auth_header, json={"bad_key": "12345"})
        assert response.status_code == 422
        assert "Prohibited config key" in response.text
        assert "bad_key" in response.text

        # now test payload with both a good key and a bad key - should be rejected
        payload["bad_key"] = "12345"
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert response.status_code == 422
        assert "Prohibited config key" in response.text
        assert "bad_key" in response.text

    def test_patch_application_config_with_invalid_value(
        self, api_client: TestClient, generate_auth_header, url
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={ACTIVE_DEFAULT_STORAGE_KEY: 33},
        )
        assert response.status_code == 422
        assert "must be a string" in response.text

        response = api_client.patch(
            url,
            headers=auth_header,
            json={ACTIVE_DEFAULT_STORAGE_KEY: "fake_storage_type"},
        )
        assert response.status_code == 422
        assert "must be one of the allowed values" in response.text

    def test_patch_application_config_empty_body(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json={},
        )
        assert response.status_code == 422
        assert "A config settings object must be provided" in response.text

        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
        )
        assert response.status_code == 422

    def test_patch_application_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        payload,
        db: Session,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings[ACTIVE_DEFAULT_STORAGE_KEY] == "s3"
        db_settings = db.query(ApplicationConfig).first()
        assert db_settings.api_set[ACTIVE_DEFAULT_STORAGE_KEY] == "s3"

        payload[ACTIVE_DEFAULT_STORAGE_KEY] = "local"
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert response_settings[ACTIVE_DEFAULT_STORAGE_KEY] == "local"
        db.refresh(db_settings)
        assert db_settings.api_set[ACTIVE_DEFAULT_STORAGE_KEY] == "local"

    # TODO: once our schema allows for more than just a single settings field,
    # we need to test that the PATCH can specify one or many settings fields
    # and only update the fields that are passed


class TestGetApplicationConfigApiSet:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    @pytest.fixture(scope="function")
    def payload(self):
        return {ACTIVE_DEFAULT_STORAGE_KEY: "s3"}

    def test_get_application_config_unauthenticated(
        self, api_client: TestClient, payload, url
    ):
        response = api_client.get(url, headers={}, json=payload)
        assert 401 == response.status_code

    def test_get_application_config_wrong_scope(
        self, api_client: TestClient, payload, url, generate_auth_header
    ):
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.get(url, headers=auth_header, json=payload)
        assert 403 == response.status_code

    def test_get_application_config_empty_settings(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
        )
        assert response.status_code == 200
        assert response.json() == {}

    def test_get_application_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
        db: Session,
        payload,
    ):
        # first we PATCH in some settings
        auth_header = generate_auth_header([scopes.CONFIG_UPDATE])
        response = api_client.patch(
            url,
            headers=auth_header,
            json=payload,
        )
        assert response.status_code == 200

        # then we test that we can GET them
        auth_header = generate_auth_header([scopes.CONFIG_READ])
        response = api_client.get(
            url,
            headers=auth_header,
            params={"api_set": True},
            json=payload,
        )
        assert response.status_code == 200
        response_settings = response.json()
        assert (
            response_settings[ACTIVE_DEFAULT_STORAGE_KEY]
            == payload[ACTIVE_DEFAULT_STORAGE_KEY]
        )


class TestGetConnections:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return urls.V1_URL_PREFIX + urls.CONFIG

    def test_get_config(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header(scopes=[scopes.CONFIG_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200

        config = resp.json()
        assert "database" in config
        assert "password" not in config["database"]
        assert "redis" in config
        assert "password" not in config["redis"]
        assert "security" in config
        security_keys = set(config["security"].keys())
        assert (
            len(
                security_keys.difference(
                    set(
                        [
                            "cors_origins",
                            "encoding",
                            "oauth_access_token_expire_minutes",
                            "subject_request_download_link_ttl_seconds",
                        ]
                    )
                )
            )
            == 0
        )
