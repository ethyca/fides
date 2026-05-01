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
        resp = api_client.post(URL, files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))})
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
        resp = api_client.post(URL, files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))})
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()

    def test_upload_rejects_oversize(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
        allow_custom_privacy_request_file_upload_enabled,
    ):
        oversize = b"%PDF" + b"x" * (DEFAULT_MAX_SIZE_BYTES + 1)
        resp = api_client.post(URL, files={"file": ("x.pdf", io.BytesIO(oversize))})
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
            URL, files={"file": ("x.pdf", io.BytesIO(b"not a real pdf"))}
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
                URL, files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))}
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
                content_length=None,
                db=db,
                service=service,
            )
        assert exc.value.status_code == 413
        assert str(DEFAULT_MAX_SIZE_BYTES) in exc.value.detail

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
            URL, files={"file": ("original.pdf", io.BytesIO(PDF_BYTES))}
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["id"].startswith("att_")

        mock_provider.upload.assert_called_once()
        kwargs = mock_provider.upload.call_args.kwargs
        assert kwargs["key"].startswith("privacy_request_attachments/")
        assert kwargs["key"].endswith(".pdf")
        assert kwargs["content_type"] == "application/pdf"
