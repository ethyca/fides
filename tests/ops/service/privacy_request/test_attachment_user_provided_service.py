"""Tests for the data-subject-uploaded attachment lifecycle.

Covers upload_attachment, resolve_file_attachments, promote_rows_to_attachments,
cleanup_orphaned_attachments, and the repository helpers.
"""

import io
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.api.schemas.redis_cache import CustomPrivacyRequestField
from fides.service.privacy_request.attachment_user_provided_repository import (
    AttachmentUserProvidedRepository,
)
from fides.service.privacy_request.attachment_user_provided_service import (
    DEFAULT_MAX_SIZE_BYTES,
    promote_rows_to_attachments,
    resolve_file_attachments,
    upload_attachment,
)

PDF_BYTES = b"%PDF-1.4 minimal pdf body"
JPEG_BYTES = b"\xff\xd8\xff\xe0 jpeg body"


@pytest.fixture
def mock_provider_result():
    """Stub for storage provider .upload() return value."""
    result = MagicMock()
    result.file_size = 123
    return result


@pytest.fixture
def mock_provider(mock_provider_result):
    """Mock storage provider with upload/download/delete methods."""
    provider = MagicMock()
    provider.upload.return_value = mock_provider_result
    provider.download.side_effect = lambda *_a, **_kw: io.BytesIO(PDF_BYTES)
    return provider


@pytest.fixture
def patch_provider_factory(mock_provider, storage_config_default):
    """Short-circuit storage lookup + provider construction.

    Other tests in the suite leak ``storage_config_default`` rows without
    teardown and the *active* default is governed by an app property — so
    relying on DB state for provider/bucket/key resolution is brittle.
    We pin all three here for deterministic assertions on bucket + key.
    """
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


class TestUploadAttachment:
    def test_upload_happy_path_creates_uploaded_row(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        result = upload_attachment(file_data=PDF_BYTES, db=db)

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

    def test_upload_rejects_oversize(self, db, storage_config_default):
        oversize = b"%PDF" + b"x" * (DEFAULT_MAX_SIZE_BYTES + 1)
        with pytest.raises(ValueError, match="maximum allowed size"):
            upload_attachment(file_data=oversize, db=db)

    def test_upload_rejects_unknown_magic(
        self, db, storage_config_default, patch_provider_factory
    ):
        with pytest.raises(ValueError, match="File type is not allowed"):
            upload_attachment(file_data=b"not a real file format", db=db)

    def test_upload_rejects_disallowed_known_magic(
        self, db, storage_config_default, patch_provider_factory
    ):
        """docx bytes are catalogued but not on the public allowlist."""
        docx_bytes = b"PK\x03\x04 docx body"
        with pytest.raises(ValueError, match="File type is not allowed"):
            upload_attachment(file_data=docx_bytes, db=db)

    def test_upload_without_storage_config_raises(self, db):
        """No active default storage config → RuntimeError.

        Deliberately does NOT use ``patch_provider_factory`` (which pins
        ``_get_provider_and_bucket``); we want the real RuntimeError path.
        """
        with patch(
            "fides.service.privacy_request.attachment_user_provided_service.get_active_default_storage_config",
            return_value=None,
        ):
            with pytest.raises(RuntimeError, match="No active default storage"):
                upload_attachment(file_data=PDF_BYTES, db=db)


class TestResolveFileAttachments:
    def test_returns_empty_when_no_fields(self, db):
        assert resolve_file_attachments(None, {"file"}, db) == []

    def test_returns_empty_when_no_declared_file_names(self, db):
        fields = {"other": CustomPrivacyRequestField(label="other", value="something")}
        assert resolve_file_attachments(fields, set(), db) == []

    def test_returns_empty_when_collection_disabled(
        self, db, allow_custom_privacy_request_field_collection_disabled
    ):
        fields = {"file": CustomPrivacyRequestField(label="file", value=["missing_id"])}
        assert resolve_file_attachments(fields, {"file"}, db) == []

    def test_happy_path_resolves_uploaded_rows(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        repo = AttachmentUserProvidedRepository(db)
        row = repo.create_uploaded(
            object_key="privacy_request_attachments/one.pdf",
            storage_key=storage_config_default.key,
        )
        db.commit()

        fields = {"file": CustomPrivacyRequestField(label="file", value=[row.id])}
        rows = resolve_file_attachments(fields, {"file"}, db)
        assert [r.id for r in rows] == [row.id]

        row.delete(db)

    def test_missing_id_raises(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        fields = {
            "file": CustomPrivacyRequestField(label="file", value=["att_missing"])
        }
        with pytest.raises(ValueError, match="expired or is invalid"):
            resolve_file_attachments(fields, {"file"}, db)

    def test_non_list_value_raises(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        fields = {"file": CustomPrivacyRequestField(label="file", value="not a list")}
        with pytest.raises(ValueError, match="must be a list"):
            resolve_file_attachments(fields, {"file"}, db)

    def test_field_not_submitted_is_skipped(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        """Declared file field not in submission → no error, just skipped."""
        fields = {"other": CustomPrivacyRequestField(label="other", value="hello")}
        assert resolve_file_attachments(fields, {"file"}, db) == []


class TestPromoteRowsToAttachments:
    def test_no_rows_is_noop(self, db, storage_config_default):
        promote_rows_to_attachments(MagicMock(), db, [])

    def test_promote_flips_status_and_creates_attachment(
        self,
        db,
        storage_config_default,
        privacy_request,
        patch_provider_factory,
        mock_provider,
    ):
        repo = AttachmentUserProvidedRepository(db)
        row = repo.create_uploaded(
            object_key="privacy_request_attachments/promote.pdf",
            storage_key=storage_config_default.key,
        )
        db.commit()

        promote_rows_to_attachments(privacy_request, db, [row])

        db.refresh(row)
        assert row.status == AttachmentUserProvidedStatus.promoted
        assert row.promoted_at is not None

        attachment_ref = (
            db.query(AttachmentReference)
            .filter(
                AttachmentReference.reference_id == privacy_request.id,
                AttachmentReference.reference_type
                == AttachmentReferenceType.privacy_request,
            )
            .first()
        )
        assert attachment_ref is not None

        attachment = (
            db.query(Attachment)
            .filter(Attachment.id == attachment_ref.attachment_id)
            .one()
        )
        assert attachment.file_name == "promote.pdf"

        mock_provider.delete.assert_called_with(
            "test_bucket", "privacy_request_attachments/promote.pdf"
        )

        # Clean up
        db.delete(attachment_ref)
        db.delete(attachment)
        row.delete(db)

    def test_promote_rejects_non_uploaded_row(
        self,
        db,
        storage_config_default,
        privacy_request,
        patch_provider_factory,
    ):
        repo = AttachmentUserProvidedRepository(db)
        row = repo.create_uploaded(
            object_key="privacy_request_attachments/bad.pdf",
            storage_key=storage_config_default.key,
        )
        row.status = AttachmentUserProvidedStatus.deleted
        db.commit()

        with pytest.raises(ValueError, match="Refusing to promote"):
            promote_rows_to_attachments(privacy_request, db, [row])

        row.delete(db)


class TestAttachmentUserProvidedRepository:
    def test_create_uploaded_flushes_without_commit(self, db, storage_config_default):
        repo = AttachmentUserProvidedRepository(db)
        row = repo.create_uploaded(
            object_key="privacy_request_attachments/flush.pdf",
            storage_key=storage_config_default.key,
        )
        assert row.id is not None
        assert row.status == AttachmentUserProvidedStatus.uploaded
        # Roll back — no commit was issued inside create_uploaded.
        db.rollback()
        assert (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == row.id)
            .first()
            is None
        )

    def test_mark_promoted_rejects_non_uploaded(self, db, storage_config_default):
        repo = AttachmentUserProvidedRepository(db)
        row = repo.create_uploaded(
            object_key="privacy_request_attachments/guard.pdf",
            storage_key=storage_config_default.key,
        )
        row.status = AttachmentUserProvidedStatus.deleted
        with pytest.raises(ValueError, match="Refusing to promote"):
            repo.mark_promoted([row])

    def test_lock_uploaded_by_ids_filters_to_uploaded(self, db, storage_config_default):
        repo = AttachmentUserProvidedRepository(db)
        uploaded = repo.create_uploaded(
            object_key="privacy_request_attachments/lock1.pdf",
            storage_key=storage_config_default.key,
        )
        deleted = repo.create_uploaded(
            object_key="privacy_request_attachments/lock2.pdf",
            storage_key=storage_config_default.key,
        )
        deleted.status = AttachmentUserProvidedStatus.deleted
        db.commit()

        rows = repo.lock_uploaded_by_ids([uploaded.id, deleted.id, "att_missing"])
        assert [r.id for r in rows] == [uploaded.id]

        uploaded.delete(db)
        deleted.delete(db)
