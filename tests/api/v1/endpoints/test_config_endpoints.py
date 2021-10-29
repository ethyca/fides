import pytest
from starlette.testclient import TestClient

from fidesops.api.v1 import (
    scope_registry as scopes,
    urn_registry as urls,
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
                            "CORS_ORIGINS",
                            "ENCODING",
                            "OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
                        ]
                    )
                )
            )
            == 0
        )
