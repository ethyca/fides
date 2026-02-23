import json
from typing import Any, Dict

from fastapi.testclient import TestClient

from fides.api.models.privacy_request.provided_identity import ProvidedIdentity
from fides.common.api.scope_registry import (
    PRIVACY_REQUEST_READ,
    STORAGE_CREATE_OR_UPDATE,
)
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_DIAGNOSTICS,
    V1_URL_PREFIX,
)


class TestPrivacyRequestDiagnostics:
    def test_diagnostics_happy_path_non_pii(
        self,
        api_client: TestClient,
        db,
        generate_auth_header,
        privacy_request,
    ) -> None:
        """Diagnostics endpoint should return 200 and exclude raw identity values."""
        identity_value = "user@example.com"
        ProvidedIdentity.create(
            db,
            data={
                "privacy_request_id": privacy_request.id,
                "field_name": "email",
                "field_label": "Email",
                "hashed_value": ProvidedIdentity.hash_value(identity_value),
                "encrypted_value": {"value": identity_value},
            },
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        url = V1_URL_PREFIX + PRIVACY_REQUEST_DIAGNOSTICS.format(
            privacy_request_id=privacy_request.id
        )

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 200

        payload: Dict[str, Any] = resp.json()
        assert payload["privacy_request"]["id"] == privacy_request.id

        # Provided identities should include presence flags, not raw values
        for ident in payload.get("provided_identities", []):
            assert "encrypted_value" not in ident
            assert "hashed_value" not in ident
            assert "encrypted_value_present" in ident
            assert "hashed_value_present" in ident

        # Strong safety check: raw identity should not appear anywhere in the response
        assert identity_value not in json.dumps(payload)

    def test_diagnostics_404(
        self,
        api_client: TestClient,
        generate_auth_header,
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        url = V1_URL_PREFIX + PRIVACY_REQUEST_DIAGNOSTICS.format(
            privacy_request_id="not-a-real-id"
        )

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 404

    def test_diagnostics_wrong_scope_403(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
    ) -> None:
        auth_header = generate_auth_header(scopes=[STORAGE_CREATE_OR_UPDATE])
        url = V1_URL_PREFIX + PRIVACY_REQUEST_DIAGNOSTICS.format(
            privacy_request_id=privacy_request.id
        )

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 403
