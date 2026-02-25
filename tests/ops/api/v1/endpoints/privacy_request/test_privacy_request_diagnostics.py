import json
from typing import Any, Dict
from unittest.mock import patch
from zipfile import ZipFile

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
from fides.service.privacy_request import (
    privacy_request_diagnostics as diagnostics_service,
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
        assert payload["download_url"]
        assert payload["object_key"].startswith("privacy-request-diagnostics/")

        # In test/dev mode, local storage is used and the "download_url" is a local file path.
        with ZipFile(payload["download_url"]) as zf:
            diagnostics_json = zf.read("diagnostics.json").decode("utf-8")
        diagnostics_payload = json.loads(diagnostics_json)

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

    def test_diagnostics_503_when_not_configured_outside_dev(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        test_config_dev_mode_disabled,
    ) -> None:
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        url = V1_URL_PREFIX + PRIVACY_REQUEST_DIAGNOSTICS.format(
            privacy_request_id=privacy_request.id
        )

        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 503
        payload: Dict[str, Any] = resp.json()
        assert (
            diagnostics_service.DEFAULT_PRIVACY_REQUEST_DIAGNOSTICS_STORAGE_KEY
            in payload["detail"]
        )
        assert "s3" in payload["detail"].lower()
        assert "gcs" in payload["detail"].lower()

    def test_diagnostics_caches_pointer_and_regenerates_url(
        self,
        api_client: TestClient,
        cache,
        generate_auth_header,
        privacy_request,
    ) -> None:
        """Second request should reuse object_key but regenerate download_url."""
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_READ])
        url = V1_URL_PREFIX + PRIVACY_REQUEST_DIAGNOSTICS.format(
            privacy_request_id=privacy_request.id
        )

        cache_key = diagnostics_service._privacy_request_diagnostics_cache_key(
            privacy_request.id
        )
        cache.delete(cache_key)

        with (
            patch.object(
                diagnostics_service,
                "get_privacy_request_diagnostics",
                wraps=diagnostics_service.get_privacy_request_diagnostics,
            ) as get_diagnostics_mock,
            patch.object(
                diagnostics_service.LocalStorageProvider,
                "generate_presigned_url",
                side_effect=["/tmp/diagnostics-url-1", "/tmp/diagnostics-url-2"],
            ),
        ):
            resp1 = api_client.get(url, headers=auth_header)
            assert resp1.status_code == 200
            payload1: Dict[str, Any] = resp1.json()

            resp2 = api_client.get(url, headers=auth_header)
            assert resp2.status_code == 200
            payload2: Dict[str, Any] = resp2.json()

        assert payload1["object_key"] == payload2["object_key"]
        assert payload1["download_url"] != payload2["download_url"]
        assert get_diagnostics_mock.call_count == 1

        cache.delete(cache_key)
