"""Tests for the unauthenticated POST /privacy-request/attachment endpoint."""

import io
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from fides.common.urn_registry import PRIVACY_REQUEST_ATTACHMENT, V1_URL_PREFIX
from fides.service.privacy_request.attachment_user_provided_service import (
    DEFAULT_MAX_SIZE_BYTES,
)

URL = V1_URL_PREFIX + PRIVACY_REQUEST_ATTACHMENT

PDF_BYTES = b"%PDF-1.4 minimal pdf body"


@pytest.fixture
def mock_provider():
    result = MagicMock(file_size=len(PDF_BYTES))
    provider = MagicMock()
    provider.upload.return_value = result
    return provider


@pytest.fixture
def patch_storage_factory(mock_provider, storage_config_default):
    """Short-circuit provider + bucket lookup so tests don't depend on
    which storage config happens to be the active default at runtime."""
    with (
        patch(
            "fides.service.privacy_request.attachment_user_provided_service.StorageProviderFactory"
        ) as factory,
        patch(
            "fides.service.privacy_request.attachment_user_provided_service._get_provider_and_bucket",
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
    ):
        resp = api_client.post(URL, files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))})
        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()

    def test_upload_rejects_oversize(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        oversize = b"%PDF" + b"x" * (DEFAULT_MAX_SIZE_BYTES + 1)
        resp = api_client.post(URL, files={"file": ("x.pdf", io.BytesIO(oversize))})
        assert resp.status_code == 413
        assert "maximum allowed size" in resp.json()["detail"]

    def test_upload_rejects_bad_magic(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
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
    ):
        with patch(
            "fides.service.privacy_request.attachment_user_provided_service.get_active_default_storage_config",
            return_value=None,
        ):
            resp = api_client.post(
                URL, files={"file": ("x.pdf", io.BytesIO(PDF_BYTES))}
            )
        assert resp.status_code == 503
        assert resp.json()["detail"] == "File attachments are temporarily unavailable."

    def test_upload_happy_path(
        self,
        api_client: TestClient,
        allow_custom_privacy_request_field_collection_enabled,
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

        # Storage upload was invoked with server-generated key under the prefix.
        mock_provider.upload.assert_called_once()
        kwargs = mock_provider.upload.call_args.kwargs
        assert kwargs["key"].startswith("privacy_request_attachments/")
        assert kwargs["key"].endswith(".pdf")
        assert kwargs["content_type"] == "application/pdf"
