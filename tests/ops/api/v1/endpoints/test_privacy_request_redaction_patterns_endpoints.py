import pytest
from starlette.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from starlette.testclient import TestClient

from fides.api.models.privacy_request_redaction_pattern import (
    PrivacyRequestRedactionPattern,
)
from fides.api.oauth.roles import (
    APPROVER,
    CONTRIBUTOR,
    OWNER,
    VIEWER,
    VIEWER_AND_APPROVER,
)
from fides.common.api import scope_registry as scopes
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_REDACTION_PATTERNS,
    V1_URL_PREFIX,
)


class TestGetPrivacyRequestRedactionPatternsEndpoints:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUEST_REDACTION_PATTERNS

    def test_get_unauthenticated(self, url: str, api_client: TestClient):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_wrong_scope(
        self, url: str, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.STORAGE_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (OWNER, HTTP_200_OK),
            (CONTRIBUTOR, HTTP_200_OK),
            (VIEWER, HTTP_403_FORBIDDEN),
            (VIEWER_AND_APPROVER, HTTP_403_FORBIDDEN),
            (APPROVER, HTTP_403_FORBIDDEN),
        ],
    )
    def test_get_by_roles(
        self, url, api_client, db, generate_role_header, role, expected_status
    ):
        # Seed some data
        PrivacyRequestRedactionPattern.replace_patterns(db=db, patterns=["user"])
        auth_header = generate_role_header(roles=[role])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == expected_status

    def test_get_empty(
        self, url: str, api_client: TestClient, generate_auth_header, db
    ):
        # Ensure empty state
        PrivacyRequestRedactionPattern.replace_patterns(db=db, patterns=[])

        auth_header = generate_auth_header(
            scopes=[scopes.PRIVACY_REQUEST_REDACTION_PATTERNS_READ]
        )
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200
        assert resp.json() == {"patterns": []}


class TestPutPrivacyRequestRedactionPatternsEndpoints:
    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + PRIVACY_REQUEST_REDACTION_PATTERNS

    def test_put_unauthenticated(self, url: str, api_client: TestClient):
        resp = api_client.put(url, json={"patterns": ["user"]})
        assert resp.status_code == 401

    def test_put_wrong_scope(
        self, url: str, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.STORAGE_READ])
        resp = api_client.put(url, headers=auth_header, json={"patterns": ["user"]})
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "role,expected_status",
        [
            (OWNER, HTTP_200_OK),
            (CONTRIBUTOR, HTTP_200_OK),
            (VIEWER, HTTP_403_FORBIDDEN),
            (VIEWER_AND_APPROVER, HTTP_403_FORBIDDEN),
            (APPROVER, HTTP_403_FORBIDDEN),
        ],
    )
    def test_put_by_roles(
        self, url, api_client, generate_role_header, role, expected_status
    ):
        auth_header = generate_role_header(roles=[role])
        resp = api_client.put(url, headers=auth_header, json={"patterns": ["user"]})
        assert resp.status_code == expected_status

    def test_put_replace_and_get(
        self, url: str, api_client: TestClient, generate_auth_header, db
    ):
        # Replace with two patterns
        auth_header_update = generate_auth_header(
            scopes=[scopes.PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE]
        )
        resp = api_client.put(
            url, headers=auth_header_update, json={"patterns": ["user", "email.*"]}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert set(body["patterns"]) == {"user", "email.*"}

        # Verify via GET
        auth_header_read = generate_auth_header(
            scopes=[scopes.PRIVACY_REQUEST_REDACTION_PATTERNS_READ]
        )
        resp_get = api_client.get(url, headers=auth_header_read)
        assert resp_get.status_code == 200
        assert set(resp_get.json()["patterns"]) == {"user", "email.*"}

        # Replace with subset + new
        resp2 = api_client.put(
            url, headers=auth_header_update, json={"patterns": ["user", "name"]}
        )
        assert resp2.status_code == 200
        assert set(resp2.json()["patterns"]) == {"user", "name"}

        # Confirm DB state
        assert set(PrivacyRequestRedactionPattern.get_patterns(db)) == {"user", "name"}

    def test_put_clear(
        self, url: str, api_client: TestClient, generate_auth_header, db
    ):
        # Seed with one pattern
        PrivacyRequestRedactionPattern.replace_patterns(db=db, patterns=["seed"])

        auth_header_update = generate_auth_header(
            scopes=[scopes.PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE]
        )
        resp = api_client.put(url, headers=auth_header_update, json={"patterns": []})
        assert resp.status_code == 200
        assert resp.json()["patterns"] == []

        # GET returns empty list as empty state
        auth_header_read = generate_auth_header(
            scopes=[scopes.PRIVACY_REQUEST_REDACTION_PATTERNS_READ]
        )
        resp_get = api_client.get(url, headers=auth_header_read)
        assert resp_get.status_code == 200
        assert resp_get.json() == {"patterns": []}

    def test_put_normalization(
        self, url: str, api_client: TestClient, generate_auth_header, db
    ):
        auth_header_update = generate_auth_header(
            scopes=[scopes.PRIVACY_REQUEST_REDACTION_PATTERNS_UPDATE]
        )
        payload = {"patterns": ["  name  ", "name", "NAME"]}
        resp = api_client.put(url, headers=auth_header_update, json=payload)
        assert resp.status_code == 200
        assert set(resp.json()["patterns"]) == {"NAME", "name"}

        # Idempotent second call
        resp = api_client.put(url, headers=auth_header_update, json=payload)
        assert resp.status_code == 200
        assert set(resp.json()["patterns"]) == {"NAME", "name"}
