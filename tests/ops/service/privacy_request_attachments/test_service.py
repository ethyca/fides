"""Tests for the upload, resolve, and promote attachment service paths."""

import io
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
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
    ORPHAN_MIN_AGE_SECONDS,
    AttachmentUserProvidedService,
    FileUploadConstraints,
    _bucket,
    _cleanup_orphaned_attachments,
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
            file_data=PDF_BYTES,
            session=db,
            constraints=FileUploadConstraints.defaults(),
            field_name="file",
            property_id="test_prop",
            policy_key="default_access_policy",
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
                file_data=PDF_BYTES,
                session=db,
                constraints=FileUploadConstraints.defaults(),
                field_name="file",
                property_id="test_prop",
                policy_key="default_access_policy",
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
                file_data=oversize,
                session=db,
                constraints=FileUploadConstraints.defaults(),
                field_name="file",
                property_id="test_prop",
                policy_key="default_access_policy",
            )

    def test_upload_rejects_unknown_magic(
        self, db, storage_config_default, patch_provider_factory
    ):
        with pytest.raises(DisallowedFileTypeError):
            AttachmentUserProvidedService().upload_attachment(
                file_data=b"not a real file format",
                session=db,
                constraints=FileUploadConstraints.defaults(),
                field_name="file",
                property_id="test_prop",
                policy_key="default_access_policy",
            )

    def test_upload_without_storage_config_raises(self, db):
        with patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.get_active_default_storage_config",
            return_value=None,
        ):
            with pytest.raises(StorageNotConfiguredError):
                AttachmentUserProvidedService().upload_attachment(
                    file_data=PDF_BYTES,
                    session=db,
                    constraints=FileUploadConstraints.defaults(),
                    field_name="file",
                    property_id="test_prop",
                    policy_key="default_access_policy",
                )

    def test_upload_respects_per_field_max_size(
        self, db, storage_config_default, patch_provider_factory
    ):
        with pytest.raises(FileTooLargeError):
            AttachmentUserProvidedService().upload_attachment(
                file_data=PDF_BYTES,
                session=db,
                constraints=FileUploadConstraints(
                    max_size_bytes=1,
                    allowed_file_types=frozenset({"pdf", "png", "jpg"}),
                ),
                field_name="file",
                property_id="test_prop",
                policy_key="default_access_policy",
            )

    def test_upload_respects_per_field_allowed_file_types(
        self, db, storage_config_default, patch_provider_factory
    ):
        with pytest.raises(DisallowedFileTypeError):
            AttachmentUserProvidedService().upload_attachment(
                file_data=PDF_BYTES,
                session=db,
                constraints=FileUploadConstraints(
                    max_size_bytes=DEFAULT_MAX_SIZE_BYTES,
                    allowed_file_types=frozenset({"png"}),
                ),
                field_name="file",
                property_id="test_prop",
                policy_key="default_access_policy",
            )

    def test_upload_zip_with_zip_only_allow_list_succeeds(
        self, db, storage_config_default, patch_provider_factory
    ):
        # Regression: ``PK\x03\x04`` matches ``docx``/``xlsx``/``zip``;
        # picking the first dict entry rejected legitimate .zip uploads
        # whose allow-list only contains ``zip``.
        result = AttachmentUserProvidedService().upload_attachment(
            file_data=b"PK\x03\x04 body",
            session=db,
            constraints=FileUploadConstraints(
                max_size_bytes=DEFAULT_MAX_SIZE_BYTES,
                allowed_file_types=frozenset({"zip"}),
            ),
            field_name="file",
            property_id="test_prop",
            policy_key="default_access_policy",
        )
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == result.id)
            .one()
        )
        assert row.object_key.endswith(".zip")
        row.delete(db)

    def test_upload_zip_family_uses_client_filename_to_disambiguate(
        self, db, storage_config_default, patch_provider_factory
    ):
        # Allow-list spans the full ZIP family; the client's claimed
        # filename extension picks among them so the recorded MIME
        # matches what the client uploaded.
        result = AttachmentUserProvidedService().upload_attachment(
            file_data=b"PK\x03\x04 body",
            session=db,
            constraints=FileUploadConstraints(
                max_size_bytes=DEFAULT_MAX_SIZE_BYTES,
                allowed_file_types=frozenset({"docx", "xlsx", "zip"}),
            ),
            field_name="file",
            property_id="test_prop",
            policy_key="default_access_policy",
            client_filename="report.xlsx",
        )
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == result.id)
            .one()
        )
        assert row.object_key.endswith(".xlsx")
        row.delete(db)

    def test_upload_falls_back_to_client_filename_when_no_magic_match(
        self, db, storage_config_default, patch_provider_factory
    ):
        # CSV / TXT have no distinctive magic prefix. Without magic
        # candidates the client filename is the only signal — accepted
        # iff the claimed extension is in the allow-list.
        result = AttachmentUserProvidedService().upload_attachment(
            file_data=b"a,b,c\n1,2,3\n",
            session=db,
            constraints=FileUploadConstraints(
                max_size_bytes=DEFAULT_MAX_SIZE_BYTES,
                allowed_file_types=frozenset({"csv"}),
            ),
            field_name="file",
            property_id="test_prop",
            policy_key="default_access_policy",
            client_filename="export.csv",
        )
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == result.id)
            .one()
        )
        assert row.object_key.endswith(".csv")
        row.delete(db)

    def test_upload_rejects_when_client_filename_not_in_allow_list(
        self, db, storage_config_default, patch_provider_factory
    ):
        # No magic match + client extension not in allow-list → reject.
        with pytest.raises(DisallowedFileTypeError):
            AttachmentUserProvidedService().upload_attachment(
                file_data=b"a,b,c\n1,2,3\n",
                session=db,
                constraints=FileUploadConstraints(
                    max_size_bytes=DEFAULT_MAX_SIZE_BYTES,
                    allowed_file_types=frozenset({"pdf"}),
                ),
                field_name="file",
                property_id="test_prop",
                policy_key="default_access_policy",
                client_filename="export.csv",
            )

    def test_upload_rejects_when_magic_match_disjoint_from_allow_list(
        self, db, storage_config_default, patch_provider_factory
    ):
        # Magic bytes match a real type (PDF) but the allow-list does
        # not include it; the client-filename fallback only applies
        # when there are no magic candidates at all.
        with pytest.raises(DisallowedFileTypeError):
            AttachmentUserProvidedService().upload_attachment(
                file_data=PDF_BYTES,
                session=db,
                constraints=FileUploadConstraints(
                    max_size_bytes=DEFAULT_MAX_SIZE_BYTES,
                    allowed_file_types=frozenset({"csv"}),
                ),
                field_name="file",
                property_id="test_prop",
                policy_key="default_access_policy",
                client_filename="anything.csv",
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
    @pytest.mark.parametrize(
        "fields, names, fixture",
        [
            pytest.param(None, {"file"}, None, id="no_fields"),
            pytest.param(
                {"o": CustomPrivacyRequestField(label="o", value="x")},
                set(),
                None,
                id="no_declared_names",
            ),
            pytest.param(
                {"file": CustomPrivacyRequestField(label="file", value=["x"])},
                {"file"},
                "allow_custom_privacy_request_field_collection_disabled",
                id="collection_disabled",
            ),
        ],
    )
    def test_returns_empty_short_circuits(self, db, request, fields, names, fixture):
        if fixture:
            request.getfixturevalue(fixture)
        assert (
            AttachmentUserProvidedService().resolve_file_attachments(
                fields,
                names,
                "test_prop",
                "default_access_policy",
                session=db,
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
            field_name="file",
            property_id="test_prop",
            policy_key="default_access_policy",
            session=db,
        )
        db.commit()

        fields = {"file": CustomPrivacyRequestField(label="file", value=[record.id])}
        rows = AttachmentUserProvidedService().resolve_file_attachments(
            fields, {"file"}, "test_prop", "default_access_policy", session=db
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
                fields, {"file"}, "test_prop", "default_access_policy", session=db
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
                fields, {"file"}, "test_prop", "default_access_policy", session=db
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
                fields, {"file"}, "test_prop", "default_access_policy", session=db
            )
            == []
        )

    @pytest.mark.parametrize(
        "uploaded, submitted",
        [
            pytest.param(
                {
                    "field_name": "other_field",
                    "property_id": "test_prop",
                    "policy_key": "default_access_policy",
                },
                {
                    "field_name": "file",
                    "property_id": "test_prop",
                    "policy_key": "default_access_policy",
                },
                id="field_name",
            ),
            pytest.param(
                {
                    "field_name": "file",
                    "property_id": "prop_uploaded",
                    "policy_key": "default_access_policy",
                },
                {
                    "field_name": "file",
                    "property_id": "prop_submitted",
                    "policy_key": "default_access_policy",
                },
                id="property_id",
            ),
            pytest.param(
                {
                    "field_name": "file",
                    "property_id": "test_prop",
                    "policy_key": "default_access_policy",
                },
                {
                    "field_name": "file",
                    "property_id": "test_prop",
                    "policy_key": "default_erasure_policy",
                },
                id="policy_key",
            ),
        ],
    )
    def test_context_mismatch_raises(
        self,
        db,
        storage_config_default,
        allow_custom_privacy_request_field_collection_enabled,
        uploaded,
        submitted,
    ):
        from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
            AttachmentContextMismatchError,
        )

        record = AttachmentUserProvidedRepository().create_uploaded(
            object_key=f"privacy_request_attachments/mismatch_{uploaded['field_name']}.pdf",
            storage_key=storage_config_default.key,
            session=db,
            **uploaded,
        )
        db.commit()

        fields = {
            submitted["field_name"]: CustomPrivacyRequestField(
                label=submitted["field_name"], value=[record.id]
            )
        }
        try:
            with pytest.raises(AttachmentContextMismatchError):
                AttachmentUserProvidedService().resolve_file_attachments(
                    fields,
                    {submitted["field_name"]},
                    submitted["property_id"],
                    submitted["policy_key"],
                    session=db,
                )
        finally:
            db.rollback()
            row = (
                db.query(AttachmentUserProvided)
                .filter(AttachmentUserProvided.id == record.id)
                .one()
            )
            row.delete(db)


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
            field_name="file",
            property_id="test_prop",
            policy_key="example_access_request_policy",
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
        privacy_request.property_id = "test_prop"
        db.commit()
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

    def test_promote_rejects_property_id_mismatch(
        self,
        db,
        storage_config_default,
        privacy_request,
        patch_provider_factory,
    ):
        from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
            AttachmentContextMismatchError,
        )

        record = AttachmentUserProvidedRepository().create_uploaded(
            object_key="privacy_request_attachments/mismatch.pdf",
            storage_key=storage_config_default.key,
            field_name="file",
            property_id="prop_uploaded",
            policy_key="example_access_request_policy",
            session=db,
        )
        db.commit()
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == record.id)
            .one()
        )
        privacy_request.property_id = "prop_submitted"
        db.commit()

        with pytest.raises(AttachmentContextMismatchError):
            AttachmentUserProvidedService().promote_rows_to_attachments(
                privacy_request, [row], session=db
            )

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
            field_name="file",
            property_id="test_prop",
            policy_key="example_access_request_policy",
            session=db,
        )
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == record.id)
            .one()
        )
        row.status = AttachmentUserProvidedStatus.deleted
        privacy_request.property_id = "test_prop"
        db.commit()

        with pytest.raises(InvalidAttachmentStateError):
            AttachmentUserProvidedService().promote_rows_to_attachments(
                privacy_request, [row], session=db
            )

        row.delete(db)

    def test_promote_multiple_rows_all_succeed(
        self,
        db,
        storage_config_default,
        privacy_request,
        patch_provider_factory,
        mock_provider,
    ):
        # Promote loop must iterate over every row, mark each ``promoted``,
        # create one Attachment per row, and best-effort delete each temp
        # object after the success path.
        repo = AttachmentUserProvidedRepository()
        records = [
            repo.create_uploaded(
                object_key=f"privacy_request_attachments/multi_{i}.pdf",
                storage_key=storage_config_default.key,
                field_name="file",
                property_id="test_prop",
                policy_key="example_access_request_policy",
                session=db,
            )
            for i in range(2)
        ]
        db.commit()
        rows = [
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == r.id)
            .one()
            for r in records
        ]

        with patch(
            "fides.service.privacy_request_attachments.privacy_request_attachments_service.AttachmentService.upload",
            return_value=None,
        ):
            AttachmentUserProvidedService().promote_rows_to_attachments(
                privacy_request, rows, session=db
            )

        for row in rows:
            db.refresh(row)
            assert row.status == AttachmentUserProvidedStatus.promoted
            assert row.promoted_at is not None

        attachment_refs = (
            db.query(AttachmentReference)
            .filter(AttachmentReference.reference_id == privacy_request.id)
            .all()
        )
        assert len(attachment_refs) == 2

        delete_keys = [c.args[1] for c in mock_provider.delete.call_args_list]
        assert sorted(delete_keys) == [
            "privacy_request_attachments/multi_0.pdf",
            "privacy_request_attachments/multi_1.pdf",
        ]

        for ref in attachment_refs:
            attachment = (
                db.query(Attachment).filter(Attachment.id == ref.attachment_id).one()
            )
            db.delete(ref)
            db.delete(attachment)
        for row in rows:
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
            field_name="file",
            property_id="test_prop",
            policy_key="example_access_request_policy",
            session=db,
        )
        rec2 = repo.create_uploaded(
            object_key="privacy_request_attachments/p2.pdf",
            storage_key=storage_config_default.key,
            field_name="file",
            property_id="test_prop",
            policy_key="example_access_request_policy",
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
        privacy_request.property_id = "test_prop"
        db.commit()
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
        policy_key="example_access_request_policy",
        property_id="test_prop",
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

        def _capture(_self, _fields, names, property_id, policy_key, *, session):
            captured["names"] = names
            captured["property_id"] = property_id
            captured["policy_key"] = policy_key
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
        assert captured["property_id"] == "test_prop"
        assert captured["policy_key"] == "example_access_request_policy"

    def test_rejects_when_property_id_missing(self, file_svc_req):
        from fides.api.common_exceptions import PrivacyRequestError

        svc, req = file_svc_req
        req = req.model_copy(update={"property_id": None})
        with pytest.raises(
            PrivacyRequestError,
            match="property_id is required when the submission includes file fields",
        ):
            svc.create_privacy_request(req, authenticated=True)

    def test_resolve_not_found_wraps_as_privacy_request_error(self, file_svc_req):
        from fides.api.common_exceptions import PrivacyRequestError

        svc, req = file_svc_req
        with patch.object(
            AttachmentUserProvidedService,
            "resolve_file_attachments",
            side_effect=AttachmentNotFoundError("doc"),
        ):
            with pytest.raises(PrivacyRequestError, match="doc"):
                svc.create_privacy_request(req, authenticated=True)

    def test_strips_file_field_keeps_non_file_field(self, file_svc_req):
        # Strip must drop the FileUpload field but preserve sibling
        # non-file fields so downstream persistence still sees them.
        from fides.api.common_exceptions import PrivacyRequestError

        svc, req = file_svc_req
        req = req.model_copy(
            update={
                "custom_privacy_request_fields": {
                    "doc": {"label": "Doc", "value": ["att_123"]},
                    "reason": {"label": "Reason", "value": "needed"},
                }
            }
        )

        captured: dict = {}

        def _capture(_db, _pr, _consent, fields):
            captured["fields"] = fields
            raise PrivacyRequestError("stop here", {})

        privacy_request = MagicMock(id="pr-1")
        policy = MagicMock(id="pol-1")
        policy.generate_masking_secrets.return_value = {}

        with (
            patch.object(
                AttachmentUserProvidedService,
                "resolve_file_attachments",
                return_value=[],
            ),
            patch(f"{_PRS}.Policy.get_by", return_value=policy),
            patch(f"{_PRS}.Property.get_by", return_value=MagicMock(id="prop-1")),
            patch(f"{_PRS}.build_required_privacy_request_kwargs", return_value={}),
            patch(f"{_PRS}.PrivacyRequest.create", return_value=privacy_request),
            patch(f"{_PRS}._create_or_update_custom_fields", side_effect=_capture),
            pytest.raises(PrivacyRequestError, match="stop here"),
        ):
            svc.create_privacy_request(req, authenticated=True)

        assert "doc" not in captured["fields"]
        assert "reason" in captured["fields"]

    def test_no_file_fields_skips_resolve_call_with_empty_names(self):
        # When the configured action has no FileUpload field, the service
        # still runs through its resolve/promote scaffolding but with an
        # empty file_field_names set, and never invokes promote.
        from fides.api.common_exceptions import PrivacyRequestError
        from fides.api.schemas.privacy_request import PrivacyRequestCreate
        from fides.api.schemas.redis_cache import Identity
        from fides.service.privacy_request.privacy_request_service import (
            PrivacyRequestService,
        )

        action = MagicMock(custom_privacy_request_fields=None)
        attachment_svc = MagicMock(spec=AttachmentUserProvidedService)
        attachment_svc.resolve_file_attachments.return_value = []
        svc = PrivacyRequestService(
            MagicMock(), MagicMock(), MagicMock(), attachment_svc
        )
        svc._resolve_privacy_center_config_dict = MagicMock(return_value=None)
        svc._parse_privacy_center_config = MagicMock(return_value=None)
        svc._get_matching_action = MagicMock(return_value=action)

        req = PrivacyRequestCreate(
            identity=Identity(email="x@y.z"),
            policy_key="default_access_policy",
        )

        with (
            patch(f"{_PRS}.Policy.get_by", return_value=None),
            pytest.raises(PrivacyRequestError, match="does not exist"),
        ):
            svc.create_privacy_request(req, authenticated=True)

        attachment_svc.resolve_file_attachments.assert_called_once()
        names_arg = attachment_svc.resolve_file_attachments.call_args.args[1]
        assert names_arg == set()
        attachment_svc.promote_rows_to_attachments.assert_not_called()


class TestResolveUploadConstraints:
    """Cover ``resolve_upload_constraints`` precedence + first-match resolution."""

    _MODULE = (
        "fides.service.privacy_request_attachments.privacy_request_attachments_service"
    )

    def _file_field(self, label, *, max_size_bytes, allowed_file_types):
        from fides.api.schemas.privacy_center_config import (
            FileUploadCustomPrivacyRequestField,
        )

        return FileUploadCustomPrivacyRequestField(
            label=label,
            max_size_bytes=max_size_bytes,
            allowed_file_types=list(allowed_file_types),
        )

    def _faux_action(self, fields, *, policy_key="default_access_policy"):
        action = MagicMock(custom_privacy_request_fields=fields)
        action.policy_key = policy_key
        return action

    def _faux_config(self, actions):
        cfg = MagicMock()
        cfg.actions = actions
        return cfg

    @contextmanager
    def _stub_config(self, cfg=None, *, config_dict={"actions": []}, parse_raises=None):
        with (
            patch(
                f"{self._MODULE}._resolve_privacy_center_config_dict",
                return_value=config_dict,
            ) as resolver,
            patch(f"{self._MODULE}.PrivacyCenterConfigSchema") as cfg_cls,
        ):
            if parse_raises:
                cfg_cls.model_validate.side_effect = parse_raises
            else:
                cfg_cls.model_validate.return_value = cfg
            yield resolver

    @pytest.mark.parametrize(
        "stub_kwargs, field_name",
        [
            pytest.param({"config_dict": None}, "passport", id="no_config"),
            pytest.param(
                {"parse_raises": ValueError("bad")}, "passport", id="unparseable_config"
            ),
            pytest.param({"cfg": "_no_match_cfg"}, "passport", id="no_matching_field"),
            pytest.param(
                {"cfg": "_text_field_cfg"},
                "passport",
                id="non_file_field_with_matching_name",
            ),
        ],
    )
    def test_returns_defaults(self, db, stub_kwargs, field_name):
        from fides.api.schemas.privacy_center_config import CustomPrivacyRequestField
        from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
            FileUploadConstraints,
            resolve_upload_constraints,
        )

        if stub_kwargs.get("cfg") == "_no_match_cfg":
            stub_kwargs["cfg"] = self._faux_config(
                [self._faux_action({"other": MagicMock()})]
            )
        elif stub_kwargs.get("cfg") == "_text_field_cfg":
            stub_kwargs["cfg"] = self._faux_config(
                [
                    self._faux_action(
                        {
                            "passport": CustomPrivacyRequestField(
                                label="Reason", field_type="text"
                            )
                        }
                    )
                ]
            )

        with self._stub_config(**stub_kwargs):
            assert (
                resolve_upload_constraints(
                    db,
                    property_id="",
                    policy_key="default_access_policy",
                    field_name=field_name,
                )
                == FileUploadConstraints.defaults()
            )

    def test_single_action_returns_field_limits(self, db):
        from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
            FileUploadConstraints,
            resolve_upload_constraints,
        )

        field = self._file_field(
            "Passport", max_size_bytes=2048, allowed_file_types=["pdf", "png"]
        )
        with self._stub_config(
            self._faux_config([self._faux_action({"passport": field})])
        ):
            assert resolve_upload_constraints(
                db,
                property_id="",
                policy_key="default_access_policy",
                field_name="passport",
            ) == FileUploadConstraints(
                max_size_bytes=2048,
                allowed_file_types=frozenset({"pdf", "png"}),
            )

    def test_property_id_passed_through(self, db):
        from fides.service.privacy_request_attachments.privacy_request_attachments_service import (
            resolve_upload_constraints,
        )

        field = self._file_field(
            "Passport", max_size_bytes=512, allowed_file_types=["pdf"]
        )
        with self._stub_config(
            self._faux_config([self._faux_action({"passport": field})])
        ) as resolver:
            resolve_upload_constraints(
                db,
                property_id="prop_xyz",
                policy_key="default_access_policy",
                field_name="passport",
            )
        resolver.assert_called_once_with(db, "prop_xyz")


class TestFileUploadConstraintsValidation:
    """Self-validation invariants enforced by ``__post_init__``."""

    @pytest.mark.parametrize(
        "max_size_bytes, allowed, match",
        [
            pytest.param(
                0,
                frozenset({"pdf"}),
                "max_size_bytes must be greater than 0",
                id="zero_size",
            ),
            pytest.param(
                -1,
                frozenset({"pdf"}),
                "max_size_bytes must be greater than 0",
                id="negative_size",
            ),
            pytest.param(
                1024,
                frozenset(),
                "allowed_file_types must not be empty",
                id="empty_allowed",
            ),
            pytest.param(
                1024,
                frozenset({"exe"}),
                "Unsupported file types",
                id="unsupported_type",
            ),
        ],
    )
    def test_rejects_invalid(self, max_size_bytes, allowed, match):
        with pytest.raises(ValueError, match=match):
            FileUploadConstraints(
                max_size_bytes=max_size_bytes, allowed_file_types=allowed
            )

    def test_defaults_pass_validation(self):
        c = FileUploadConstraints.defaults()
        assert c.max_size_bytes > 0
        assert c.allowed_file_types


def _make_uploaded_row(db, storage_config, *, age_seconds: int, suffix: str):
    """Insert an ``uploaded`` row and back-date its ``created_at``."""
    record = AttachmentUserProvidedRepository().create_uploaded(
        object_key=f"privacy_request_attachments/{suffix}.pdf",
        storage_key=storage_config.key,
        field_name="file",
        property_id="test_prop",
        policy_key="example_access_request_policy",
        session=db,
    )
    row = (
        db.query(AttachmentUserProvided)
        .filter(AttachmentUserProvided.id == record.id)
        .one()
    )
    row.created_at = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    db.commit()
    return row


class TestCleanupOrphanedAttachments:
    """Cover ``_cleanup_orphaned_attachments`` orphan-sweep semantics."""

    def test_deletes_uploaded_rows_older_than_cutoff(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        # Storage object deleted, row CAS'd uploaded → deleted.
        old = _make_uploaded_row(
            db,
            storage_config_default,
            age_seconds=ORPHAN_MIN_AGE_SECONDS + 60,
            suffix="orphan",
        )

        _cleanup_orphaned_attachments(db)

        db.refresh(old)
        assert old.status == AttachmentUserProvidedStatus.deleted
        mock_provider.delete.assert_called_once_with(
            "test_bucket", "privacy_request_attachments/orphan.pdf"
        )

        old.delete(db)

    def test_skips_rows_younger_than_cutoff(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        young = _make_uploaded_row(
            db,
            storage_config_default,
            age_seconds=ORPHAN_MIN_AGE_SECONDS - 60,
            suffix="fresh",
        )

        _cleanup_orphaned_attachments(db)

        db.refresh(young)
        assert young.status == AttachmentUserProvidedStatus.uploaded
        mock_provider.delete.assert_not_called()

        young.delete(db)

    def test_skips_already_promoted_rows(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        # Promoted rows must not be touched even if older than the cutoff.
        promoted = _make_uploaded_row(
            db,
            storage_config_default,
            age_seconds=ORPHAN_MIN_AGE_SECONDS + 60,
            suffix="claimed",
        )
        promoted.status = AttachmentUserProvidedStatus.promoted
        db.commit()

        _cleanup_orphaned_attachments(db)

        db.refresh(promoted)
        assert promoted.status == AttachmentUserProvidedStatus.promoted
        mock_provider.delete.assert_not_called()

        promoted.delete(db)

    def test_keeps_row_in_uploaded_when_storage_delete_fails(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        # If we cannot delete the bytes, leave the row in ``uploaded`` so
        # the next sweep retries — never advance to ``deleted`` while the
        # object is still live.
        mock_provider.delete.side_effect = RuntimeError("s3 down")
        old = _make_uploaded_row(
            db,
            storage_config_default,
            age_seconds=ORPHAN_MIN_AGE_SECONDS + 60,
            suffix="stuck",
        )

        _cleanup_orphaned_attachments(db)

        db.refresh(old)
        assert old.status == AttachmentUserProvidedStatus.uploaded

        old.delete(db)

    def test_short_circuits_when_no_storage_config(self, db, storage_config_default):
        # Function returns cleanly without iterating rows when storage is
        # not configured — re-running once configured does the work.
        old = _make_uploaded_row(
            db,
            storage_config_default,
            age_seconds=ORPHAN_MIN_AGE_SECONDS + 60,
            suffix="no_storage",
        )

        with patch(
            "fides.service.privacy_request_attachments."
            "privacy_request_attachments_service.get_active_default_storage_config",
            return_value=None,
        ):
            _cleanup_orphaned_attachments(db)

        db.refresh(old)
        assert old.status == AttachmentUserProvidedStatus.uploaded

        old.delete(db)

    def test_one_failure_does_not_abort_batch(
        self,
        db,
        storage_config_default,
        patch_provider_factory,
        mock_provider,
    ):
        # First delete raises, second succeeds — second row must still be
        # transitioned to ``deleted``.
        first = _make_uploaded_row(
            db,
            storage_config_default,
            age_seconds=ORPHAN_MIN_AGE_SECONDS + 120,
            suffix="bad",
        )
        second = _make_uploaded_row(
            db,
            storage_config_default,
            age_seconds=ORPHAN_MIN_AGE_SECONDS + 60,
            suffix="good",
        )

        deleted_keys: list[str] = []

        def _maybe_fail(_bucket: str, key: str) -> None:
            deleted_keys.append(key)
            if key.endswith("bad.pdf"):
                raise RuntimeError("s3 transient")

        mock_provider.delete.side_effect = _maybe_fail

        _cleanup_orphaned_attachments(db)

        db.refresh(first)
        db.refresh(second)
        assert first.status == AttachmentUserProvidedStatus.uploaded
        assert second.status == AttachmentUserProvidedStatus.deleted
        assert sorted(deleted_keys) == [
            "privacy_request_attachments/bad.pdf",
            "privacy_request_attachments/good.pdf",
        ]

        first.delete(db)
        second.delete(db)
