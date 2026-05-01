"""Tests for AttachmentUserProvidedRepository.create_uploaded."""

from fides.api.models.attachment import (
    AttachmentUserProvided,
    AttachmentUserProvidedStatus,
)
from fides.service.privacy_request_attachments.privacy_request_attachments_repository import (
    AttachmentUserProvidedRepository,
)


class TestAttachmentUserProvidedRepository:
    def test_create_uploaded_persists_row(self, db, storage_config_default):
        record = AttachmentUserProvidedRepository().create_uploaded(
            object_key="privacy_request_attachments/flush.pdf",
            storage_key=storage_config_default.key,
            field_name="passport",
            property_id="prop_xyz",
            policy_key="default_access_policy",
            session=db,
        )
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
