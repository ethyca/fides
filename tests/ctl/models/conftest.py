from io import BytesIO

import pytest

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
)


@pytest.fixture
def multiple_attachments(s3_client, db, attachment_data, user, monkeypatch):
    """Creates multiple attachments."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr(
        "fides.api.service.storage.s3.get_s3_client", mock_get_s3_client
    )

    attachment_data["user_id"] = user.id
    attachment_data["file_name"] = "file_1.txt"
    attachment_1 = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=BytesIO(b"file content 1")
    )

    attachment_data["file_name"] = "file_2.txt"
    attachment_2 = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=BytesIO(b"file content 2")
    )

    attachment_data["file_name"] = "file_3.txt"
    attachment_3 = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=BytesIO(b"file content 3")
    )

    yield attachment_1, attachment_2, attachment_3
    try:
        attachment_1.delete(db)
        attachment_2.delete(db)
        attachment_3.delete(db)
    except Exception:
        pass


@pytest.fixture
def attachment_reference(db, attachment):
    """Creates an attachment reference."""
    attachment_reference = AttachmentReference.create(
        db=db,
        data={
            "attachment_id": attachment.id,
            "reference_id": "ref_1",
            "reference_type": AttachmentReferenceType.privacy_request,
        },
    )
    yield attachment_reference
