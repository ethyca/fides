import json
from io import BytesIO
from typing import Any, Dict
from zipfile import ZipFile

from fastapi.testclient import TestClient

from fides.api.models.privacy_request.provided_identity import ProvidedIdentity
from fides.common.scope_registry import (
    PRIVACY_REQUEST_READ,
    STORAGE_CREATE_OR_UPDATE,
)
from fides.common.urn_registry import (
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
        """Diagnostics endpoint should return a ZIP and exclude raw identity values."""
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
        assert resp.headers["content-type"] == "application/zip"
        assert "attachment" in resp.headers["content-disposition"]
        assert resp.headers["content-length"] == str(len(resp.content))

        with ZipFile(BytesIO(resp.content)) as zf:
            diagnostics_json = zf.read("diagnostics.json").decode("utf-8")
        diagnostics_payload: Dict[str, Any] = json.loads(diagnostics_json)

        assert diagnostics_payload["privacy_request"]["id"] == privacy_request.id

        # Provided identities should include presence flags, not raw values
        for ident in diagnostics_payload.get("provided_identities", []):
            assert "encrypted_value" not in ident
            assert "hashed_value" not in ident
            assert "encrypted_value_present" in ident
            assert "hashed_value_present" in ident

        # Strong safety check: raw identity should not appear anywhere in the response
        assert identity_value not in diagnostics_json

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
