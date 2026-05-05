"""Tests for AttachmentUserProvidedRepository."""

from datetime import datetime, timedelta, timezone

import pytest

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_exceptions import (
    InvalidAttachmentStateError,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_repository import (
    AttachmentUserProvidedRepository,
)


def _create(db, storage_config, *, suffix: str = "flush"):
    return AttachmentUserProvidedRepository().create_uploaded(
        object_key=f"privacy_request_attachments/{suffix}.pdf",
        storage_key=storage_config.key,
        field_name="passport",
        property_id="prop_xyz",
        policy_key="default_access_policy",
        session=db,
    )


class TestAttachmentUserProvidedRepository:
    def test_create_uploaded_persists_row(self, db, storage_config_default):
        record = _create(db, storage_config_default)
        assert record.id is not None
        assert record.status == AttachmentUserProvidedStatus.uploaded
        assert record.storage_key == storage_config_default.key
        assert record.object_key == "privacy_request_attachments/flush.pdf"
        assert record.field_name == "passport"
        assert record.property_id == "prop_xyz"
        assert record.policy_key == "default_access_policy"

        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == record.id)
            .one()
        )
        row.delete(db)

    def test_list_uploaded_older_than_returns_only_old_uploaded(
        self, db, storage_config_default
    ):
        repo = AttachmentUserProvidedRepository()
        old_record = _create(db, storage_config_default, suffix="old")
        new_record = _create(db, storage_config_default, suffix="new")
        old_row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == old_record.id)
            .one()
        )
        new_row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == new_record.id)
            .one()
        )
        old_row.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()

        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        rows = repo.list_uploaded_older_than(cutoff, session=db)
        ids = {r.id for r in rows}
        assert old_row.id in ids
        assert new_row.id not in ids

        old_row.delete(db)
        new_row.delete(db)

    def test_list_uploaded_older_than_excludes_non_uploaded(
        self, db, storage_config_default
    ):
        # Promoted/deleted rows must never come back from this query — they
        # are out of scope for the orphan sweep.
        repo = AttachmentUserProvidedRepository()
        promoted_record = _create(db, storage_config_default, suffix="promoted")
        promoted_row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == promoted_record.id)
            .one()
        )
        promoted_row.status = AttachmentUserProvidedStatus.promoted
        promoted_row.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()

        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        rows = repo.list_uploaded_older_than(cutoff, session=db)
        assert promoted_row.id not in {r.id for r in rows}

        promoted_row.delete(db)

    def test_mark_deleted_transitions_uploaded_row(self, db, storage_config_default):
        repo = AttachmentUserProvidedRepository()
        record = _create(db, storage_config_default, suffix="del")
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == record.id)
            .one()
        )

        repo.mark_deleted(row, session=db)
        db.commit()

        db.refresh(row)
        assert row.status == AttachmentUserProvidedStatus.deleted

        row.delete(db)

    def test_mark_deleted_rejects_non_uploaded_row(self, db, storage_config_default):
        # Concurrent promotion guard — never overwrite a ``promoted`` row.
        repo = AttachmentUserProvidedRepository()
        record = _create(db, storage_config_default, suffix="claimed")
        row = (
            db.query(AttachmentUserProvided)
            .filter(AttachmentUserProvided.id == record.id)
            .one()
        )
        row.status = AttachmentUserProvidedStatus.promoted
        db.commit()

        with pytest.raises(InvalidAttachmentStateError):
            repo.mark_deleted(row, session=db)

        row.delete(db)
