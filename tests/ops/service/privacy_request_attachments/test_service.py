"""Tests for the upload service. Resolution + promotion ship in ENG-3517-1."""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    DisallowedFileTypeError,
    FileTooLargeError,
    StorageBucketNotConfiguredError,
    StorageNotConfiguredError,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
    DEFAULT_MAX_SIZE_BYTES,
    AttachmentUserProvidedService,
    _bucket,
    _get_provider_and_bucket,
)

PDF_BYTES = b"%PDF-1.4 minimal pdf body"


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.upload.return_value = MagicMock(file_size=123)
    return provider


@pytest.fixture
def patch_provider_factory(mock_provider, storage_config_default):
    """Pin provider/bucket/storage_config for deterministic asserts."""
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


class TestUploadAttachment:
    def test_upload_happy_path_creates_uploaded_row(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        result = AttachmentUserProvidedService().upload_attachment(
            file_data=PDF_BYTES, session=db
        )

        assert result.id.startswith("att_")
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == result.id)
            .one()
        )
        assert row.status == AttachmentUserProvidedStatus.uploaded
        assert row.storage_key == storage_config_default.key
        assert row.object_key.startswith("privacy_request_attachments/")
        assert row.object_key.endswith(".pdf")

        mock_provider.upload.assert_called_once()
        kwargs = mock_provider.upload.call_args.kwargs
        assert kwargs["content_type"] == "application/pdf"

        row.delete(db)

    def test_storage_upload_failure_rolls_back_row(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        """Row is flushed before upload; if upload raises, the row must
        not be committed (no orphan file, no orphan row)."""
        mock_provider.upload.side_effect = RuntimeError("s3 boom")

        before = db.query(AttachmentUserProvided).count()
        with pytest.raises(RuntimeError, match="s3 boom"):
            AttachmentUserProvidedService().upload_attachment(
                file_data=PDF_BYTES, session=db
            )
        # Caller-supplied session: decorator only flushes; row should not
        # be visible after the rollback we trigger to clear the failed
        # state.
        db.rollback()
        after = db.query(AttachmentUserProvided).count()
        assert after == before

    def test_upload_rejects_oversize(self, db, storage_config_default):
        oversize = b"%PDF" + b"x" * (DEFAULT_MAX_SIZE_BYTES + 1)
        with pytest.raises(FileTooLargeError):
            AttachmentUserProvidedService().upload_attachment(
                file_data=oversize, session=db
            )

    def test_upload_rejects_unknown_magic(
        self, db, storage_config_default, patch_provider_factory
    ):
        with pytest.raises(DisallowedFileTypeError):
            AttachmentUserProvidedService().upload_attachment(
                file_data=b"not a real file format", session=db
            )

    def test_upload_without_storage_config_raises(self, db):
        with patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.get_active_default_storage_config",
            return_value=None,
        ):
            with pytest.raises(StorageNotConfiguredError):
                AttachmentUserProvidedService().upload_attachment(
                    file_data=PDF_BYTES, session=db
                )


class TestProviderHelpers:
    def test_bucket_returns_value_from_details(self):
        config = MagicMock(details={"bucket": "my-bucket"})
        assert _bucket(config) == "my-bucket"

    def test_bucket_handles_none_details(self):
        config = MagicMock(details=None)
        assert _bucket(config) == ""

    def test_get_provider_and_bucket_happy_path(self, db, mock_provider):
        config = MagicMock(details={"bucket": "happy-bucket"})
        with (
            patch(
                "fides.service.privacy_request_attachments.privacy_request_attachments_service.get_active_default_storage_config",
                return_value=config,
            ),
            patch(
                "fides.service.privacy_request_attachments.privacy_request_attachments_service.StorageProviderFactory.create",
                return_value=mock_provider,
            ),
        ):
            provider, bucket, returned_config = _get_provider_and_bucket(db)
        assert provider is mock_provider
        assert bucket == "happy-bucket"
        assert returned_config is config

    def test_get_provider_and_bucket_no_bucket_raises(self, db):
        config = MagicMock(details={})
        with patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.get_active_default_storage_config",
            return_value=config,
        ):
            with pytest.raises(StorageBucketNotConfiguredError):
                _get_provider_and_bucket(db)
