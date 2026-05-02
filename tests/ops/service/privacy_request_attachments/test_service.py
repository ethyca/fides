"""Tests for the upload, resolve, and promote attachment service paths."""

import io
from unittest.mock import MagicMock, patch

import pytest

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.api.schemas.redis_cache import CustomPrivacyRequestField
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    AttachmentNotFoundError,
    DisallowedFileTypeError,
    FileTooLargeError,
    InvalidAttachmentStateError,
    InvalidAttachmentValueError,
    StorageBucketNotConfiguredError,
    StorageNotConfiguredError,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_repository import (
    AttachmentUserProvidedRepository,
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
    provider.download.side_effect = lambda *_a, **_kw: io.BytesIO(PDF_BYTES)
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

    def test_get_provider_and_bucket_local_no_bucket_ok(self, db, mock_provider):
        from fides.api.schemas.storage.storage import StorageType

        config = MagicMock(details={}, type=StorageType.local)
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
        assert bucket == ""
        assert returned_config is config


class TestResolveFileAttachments:
    def test_returns_empty_when_no_fields(self, db):
        assert (
            AttachmentUserProvidedService().resolve_file_attachments(
                None, {"file"}, session=db
            )
            == []
        )

    def test_returns_empty_when_no_declared_names(self, db):
        fields = {"o": CustomPrivacyRequestField(label="o", value="x")}
        assert (
            AttachmentUserProvidedService().resolve_file_attachments(
                fields, set(), session=db
            )
            == []
        )

    def test_returns_empty_when_collection_disabled(
        self, db, allow_custom_privacy_request_field_collection_disabled
    ):
        fields = {"file": CustomPrivacyRequestField(label="file", value=["x"])}
        assert (
            AttachmentUserProvidedService().resolve_file_attachments(
                fields, {"file"}, session=db
            )
            == []
        )

    def test_happy_path_resolves_uploaded_rows(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        record = AttachmentUserProvidedRepository().create_uploaded(
            object_key="privacy_request_attachments/one.pdf",
            storage_key=storage_config_default.key,
            session=db,
        )
        db.commit()

        fields = {"file": CustomPrivacyRequestField(label="file", value=[record.id])}
        rows = AttachmentUserProvidedService().resolve_file_attachments(
            fields, {"file"}, session=db
        )
        assert [r.id for r in rows] == [record.id]

        rows[0].delete(db)

    def test_missing_id_raises(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        fields = {
            "file": CustomPrivacyRequestField(label="file", value=["att_missing"])
        }
        with pytest.raises(AttachmentNotFoundError):
            AttachmentUserProvidedService().resolve_file_attachments(
                fields, {"file"}, session=db
            )

    def test_non_list_value_raises(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
    ):
        fields = {"file": CustomPrivacyRequestField(label="file", value="not a list")}
        with pytest.raises(InvalidAttachmentValueError):
            AttachmentUserProvidedService().resolve_file_attachments(
                fields, {"file"}, session=db
            )

    @pytest.mark.parametrize(
        "fields",
        [
            {"other": CustomPrivacyRequestField(label="other", value="hi")},
            {"file": CustomPrivacyRequestField(label="file", value=[])},
        ],
    )
    def test_skipped_paths(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
        fields,
    ):
        assert (
            AttachmentUserProvidedService().resolve_file_attachments(
                fields, {"file"}, session=db
            )
            == []
        )


class TestPromoteRowsToAttachments:
    def test_no_rows_is_noop(self, db, storage_config_default):
        AttachmentUserProvidedService().promote_rows_to_attachments(
            MagicMock(), [], session=db
        )

    @pytest.mark.parametrize("delete_raises", [False, True], ids=["clean", "raises"])
    def test_promote_flips_status_and_creates_attachment(
        self,
        db,
        storage_config_default,
        privacy_request,
        patch_provider_factory,
        mock_provider,
        delete_raises,
    ):
        # ``delete_raises=True`` exercises the Phase-3 try/except (logged-only).
        record = AttachmentUserProvidedRepository().create_uploaded(
            object_key="privacy_request_attachments/promote.pdf",
            storage_key=storage_config_default.key,
            session=db,
        )
        db.commit()
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == record.id)
            .one()
        )
        if delete_raises:
            mock_provider.delete.side_effect = RuntimeError("storage offline")
        # AttachmentService.upload would hit S3 — short-circuit it.
        with patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.AttachmentService.upload",
            return_value=None,
        ):
            AttachmentUserProvidedService().promote_rows_to_attachments(
                privacy_request, [row], session=db
            )
        db.refresh(row)
        assert row.status == AttachmentUserProvidedStatus.promoted
        assert row.promoted_at is not None
        attachment_ref = (
            db.query(AttachmentReference)
            .filter(AttachmentReference.reference_id == privacy_request.id)
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
        record = AttachmentUserProvidedRepository().create_uploaded(
            object_key="privacy_request_attachments/bad.pdf",
            storage_key=storage_config_default.key,
            session=db,
        )
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == record.id)
            .one()
        )
        row.status = AttachmentUserProvidedStatus.deleted
        db.commit()

        with pytest.raises(InvalidAttachmentStateError):
            AttachmentUserProvidedService().promote_rows_to_attachments(
                privacy_request, [row], session=db
            )

        row.delete(db)

    @pytest.mark.parametrize("cleanup_raises", [False, True], ids=["clean", "raises"])
    def test_promote_rolls_back_partial_attachments_on_failure(
        self,
        db,
        storage_config_default,
        privacy_request,
        patch_provider_factory,
        cleanup_raises,
    ):
        # Second create_and_upload raises → cleanup loop deletes the first.
        # ``cleanup_raises`` exercises the inner try/except in that loop.
        repo = AttachmentUserProvidedRepository()
        rec1 = repo.create_uploaded(
            object_key="privacy_request_attachments/p1.pdf",
            storage_key=storage_config_default.key,
            session=db,
        )
        rec2 = repo.create_uploaded(
            object_key="privacy_request_attachments/p2.pdf",
            storage_key=storage_config_default.key,
            session=db,
        )
        db.commit()
        row1 = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == rec1.id)
            .one()
        )
        row2 = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == rec2.id)
            .one()
        )

        first = MagicMock(id="att_partial")
        with patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.AttachmentService"
        ) as svc_cls:
            instance = svc_cls.return_value
            instance.create_and_upload.side_effect = [first, RuntimeError("boom")]
            if cleanup_raises:
                instance.delete.side_effect = RuntimeError("cleanup boom")
            with pytest.raises(RuntimeError, match="boom"):
                AttachmentUserProvidedService().promote_rows_to_attachments(
                    privacy_request, [row1, row2], session=db
                )
            instance.delete.assert_called_once_with(first)

        # Both rows must remain ``uploaded`` after the failure: the first
        # was flipped to ``promoted`` mid-loop and must be rolled back so a
        # caller commit cannot persist a ``promoted`` row pointing at the
        # Attachment we just deleted; the second never got that far.
        assert row1.status == AttachmentUserProvidedStatus.uploaded
        assert row1.promoted_at is None
        assert row2.status == AttachmentUserProvidedStatus.uploaded
        assert row2.promoted_at is None

        row1.delete(db)
        row2.delete(db)


_PRS = "fides.service.privacy_request.privacy_request_service"


@pytest.fixture
def file_svc_req():
    from fides.api.schemas.privacy_center_config import (
        FileUploadCustomPrivacyRequestField,
    )
    from fides.api.schemas.privacy_request import PrivacyRequestCreate
    from fides.api.schemas.redis_cache import Identity
    from fides.service.privacy_request.privacy_request_service import (
        PrivacyRequestService,
    )

    action = MagicMock(
        custom_privacy_request_fields={
            "doc": FileUploadCustomPrivacyRequestField(label="Doc")
        }
    )
    svc = PrivacyRequestService(
        MagicMock(), MagicMock(), MagicMock(), AttachmentUserProvidedService()
    )
    svc._resolve_privacy_center_config_dict = MagicMock(return_value={"x": 1})
    svc._parse_privacy_center_config = MagicMock(return_value=MagicMock())
    svc._get_matching_action = MagicMock(return_value=action)
    svc._validate_field_visibility = MagicMock()
    return svc, PrivacyRequestCreate(
        identity=Identity(email="x@y.z"),
        policy_key="default_access_policy",
        custom_privacy_request_fields={"doc": {"label": "Doc", "value": ["att_123"]}},
    )


class TestCreatePrivacyRequestFileResolution:
    def test_resolve_value_error_raises(self, file_svc_req):
        from fides.api.common_exceptions import PrivacyRequestError

        svc, req = file_svc_req
        with patch.object(
            AttachmentUserProvidedService,
            "resolve_file_attachments",
            side_effect=InvalidAttachmentValueError("doc"),
        ):
            with pytest.raises(PrivacyRequestError, match="doc"):
                svc.create_privacy_request(req, authenticated=True)

    def test_file_fields_stripped(self, file_svc_req):
        from fides.api.common_exceptions import PrivacyRequestError

        svc, req = file_svc_req
        captured: dict = {}

        def _capture(_self, _fields, names, *, session):
            captured["names"] = names
            return []

        with (
            patch.object(
                AttachmentUserProvidedService,
                "resolve_file_attachments",
                _capture,
            ),
            patch(f"{_PRS}.Policy.get_by", return_value=None),
            pytest.raises(PrivacyRequestError, match="does not exist"),
        ):
            svc.create_privacy_request(req, authenticated=True)
        assert captured["names"] == {"doc"}
