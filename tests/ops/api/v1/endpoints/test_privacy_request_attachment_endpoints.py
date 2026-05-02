"""Tests for POST /privacy-request/attachment."""

import io
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from fides.common.urn_registry import PRIVACY_REQUEST_ATTACHMENT, V1_URL_PREFIX
from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
    DEFAULT_MAX_SIZE_BYTES,
)

URL = V1_URL_PREFIX + PRIVACY_REQUEST_ATTACHMENT
PDF_BYTES = b"%PDF-1.4 minimal pdf body"


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.upload.return_value = MagicMock(file_size=len(PDF_BYTES))
    return provider


@pytest.fixture
def patch_storage_factory(mock_provider, storage_config_default):
    with (
        patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.StorageProviderFactory"
        ) as factory,
        patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service._get_provider_and_bucket",
            return_value=(mock_provider, "test_bucket", storage_config_default),
        ),
    ):
        factory.create.return_value = mock_provider
        yield factory


class TestPostPrivacyRequestAttachment:
    def test_upload_forbidden_when_custom_fields_disabled(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_disabled,
        allow_custom_privacy_request_file_upload_enabled,
    ):
        # File-upload flag alone is insufficient; field-collection must
        # also be on.
        resp = api_client.post(
            URL,
            files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))},
            data={"property_id": "p", "policy_key": "k", "field_name": "f"},
        )
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()

    def test_upload_forbidden_when_file_upload_disabled(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_disabled,
    ):
        # Field-collection alone is insufficient; file-upload flag is
        # an independent gate.
        resp = api_client.post(
            URL,
            files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))},
            data={"property_id": "p", "policy_key": "k", "field_name": "f"},
        )
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()

    def test_upload_rejects_oversize(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
    ):
        oversize = b"%PDF" + b"x" * (DEFAULT_MAX_SIZE_BYTES + 1)
        resp = api_client.post(
            URL,
            files={"file": ("x.pdf", io.BytesIO(oversize))},
            data={"property_id": "p", "policy_key": "k", "field_name": "f"},
        )
        assert resp.status_code == 413
        assert "maximum allowed size" in resp.json()["detail"]

    def test_upload_rejects_bad_magic(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
        storage_config_default,
        patch_storage_factory,
    ):
        resp = api_client.post(
            URL,
            files={"file": ("x.pdf", io.BytesIO(b"not a real pdf"))},
            data={"property_id": "p", "policy_key": "k", "field_name": "f"},
        )
        assert resp.status_code == 400
        assert "not allowed" in resp.json()["detail"]

    def test_upload_returns_503_without_storage_config(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
    ):
        with patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.get_active_default_storage_config",
            return_value=None,
        ):
            resp = api_client.post(
                URL,
                files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))},
                data={"property_id": "p", "policy_key": "k", "field_name": "f"},
            )
        assert resp.status_code == 503
        assert resp.json()["detail"] == "File attachments are temporarily unavailable."

    def test_upload_rejects_streaming_oversize_when_content_length_lies(
        self,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
        db,
    ):
        # Lying Content-Length bypasses pre-check; streaming guard fires.
        from fastapi import HTTPException

        from fides.api.v1.endpoints.privacy_request_attachment_endpoints import (
            upload_privacy_request_attachment,
        )

        upload = MagicMock()
        upload.file.read.side_effect = [
            b"%PDF" + b"x" * (DEFAULT_MAX_SIZE_BYTES + 1),
            b"",
        ]
        with pytest.raises(HTTPException) as exc:
            upload_privacy_request_attachment(
                request=MagicMock(),
                response=MagicMock(),
                file=upload,
                property_id="p",
                policy_key="k",
                field_name="f",
                content_length=1,
                db=db,
                service=MagicMock(),
            )
        assert exc.value.status_code == 413

    def test_upload_returns_413_when_service_raises_file_too_large(
        self,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
        db,
    ):
        """Service-raised ``FileTooLargeError`` maps to HTTP 413.

        The streaming guard normally fires first, so the only way to
        reach the service-side size check from the endpoint is to pass
        the streaming guard and have the service raise. We mock the
        service directly to cover the except branch.
        """
        from fastapi import HTTPException

        from fides.api.v1.endpoints.privacy_request_attachment_endpoints import (
            upload_privacy_request_attachment,
        )
        from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
            FileTooLargeError,
        )

        upload = MagicMock()
        upload.file.read.side_effect = [PDF_BYTES, b""]
        service = MagicMock()
        service.upload_attachment.side_effect = FileTooLargeError(
            DEFAULT_MAX_SIZE_BYTES
        )

        with pytest.raises(HTTPException) as exc:
            upload_privacy_request_attachment(
                request=MagicMock(),
                response=MagicMock(),
                file=upload,
                property_id="p",
                policy_key="k",
                field_name="f",
                content_length=None,
                db=db,
                service=service,
            )
        assert exc.value.status_code == 413
        assert str(DEFAULT_MAX_SIZE_BYTES) in exc.value.detail

    def test_upload_rejects_missing_property_id(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
    ):
        resp = api_client.post(
            URL,
            files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))},
            data={"policy_key": "k", "field_name": "f"},
        )
        assert resp.status_code == 422

    def test_upload_rejects_missing_policy_key(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
    ):
        resp = api_client.post(
            URL,
            files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))},
            data={"property_id": "p", "field_name": "f"},
        )
        assert resp.status_code == 422

    def test_upload_rejects_missing_field_name(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
    ):
        resp = api_client.post(
            URL,
            files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))},
            data={"property_id": "p", "policy_key": "k"},
        )
        assert resp.status_code == 422

    def test_upload_happy_path(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
        storage_config_default,
        patch_storage_factory,
        mock_provider,
    ):
        resp = api_client.post(
            URL,
            files={"file": ("original.pdf", io.BytesIO(PDF_BYTES))},
            data={"property_id": "p", "policy_key": "k", "field_name": "f"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["id"].startswith("att_")

        mock_provider.upload.assert_called_once()
        kwargs = mock_provider.upload.call_args.kwargs
        assert kwargs["key"].startswith("privacy_request_attachments/")
        assert kwargs["key"].endswith(".pdf")
        assert kwargs["content_type"] == "application/pdf"

    def test_upload_passes_property_id_policy_key_field_name_to_resolver(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
        storage_config_default,
        patch_storage_factory,
    ):
        from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
            FileUploadConstraints,
        )

        with patch(
            "fides.api.v1.endpoints.privacy_request_attachment_endpoints.resolve_upload_constraints",
            return_value=FileUploadConstraints.defaults(),
        ) as resolver:
            resp = api_client.post(
                URL,
                files={"file": ("original.pdf", io.BytesIO(PDF_BYTES))},
                data={
                    "property_id": "prop_xyz",
                    "policy_key": "default_access_policy",
                    "field_name": "passport",
                },
            )
        assert resp.status_code == 200, resp.text
        resolver.assert_called_once()
        kwargs = resolver.call_args.kwargs
        assert kwargs == {
            "property_id": "prop_xyz",
            "policy_key": "default_access_policy",
            "field_name": "passport",
        }

    def test_upload_rejects_per_field_oversize_via_content_length(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
        storage_config_default,
    ):
        from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
            FileUploadConstraints,
        )

        # Per-field cap of 8 bytes via the resolver — Content-Length pre-check
        # fires before any streaming or service call.
        with patch(
            "fides.api.v1.endpoints.privacy_request_attachment_endpoints.resolve_upload_constraints",
            return_value=FileUploadConstraints(
                max_size_bytes=8,
                allowed_file_types=frozenset({"pdf", "png", "jpg"}),
            ),
        ):
            resp = api_client.post(
                URL,
                files={"file": ("original.pdf", io.BytesIO(PDF_BYTES))},
                data={"field_name": "passport"},
            )
        assert resp.status_code == 413
        assert "8 bytes" in resp.json()["detail"]

    def test_upload_rejects_per_field_disallowed_file_type(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
        storage_config_default,
        patch_storage_factory,
    ):
        from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
            FileUploadConstraints,
        )

        # PDF passes platform allow list; per-field allow list excludes PDF.
        with patch(
            "fides.api.v1.endpoints.privacy_request_attachment_endpoints.resolve_upload_constraints",
            return_value=FileUploadConstraints(
                max_size_bytes=DEFAULT_MAX_SIZE_BYTES,
                allowed_file_types=frozenset({"png"}),
            ),
        ):
            resp = api_client.post(
                URL,
                files={"file": ("original.pdf", io.BytesIO(PDF_BYTES))},
                data={
                    "property_id": "p",
                    "policy_key": "k",
                    "field_name": "headshot",
                },
            )
        assert resp.status_code == 400
        assert "not allowed" in resp.json()["detail"]
