import pytest

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)


@pytest.fixture
def attachment_data(user, storage_config):
    """Returns attachment data."""
    return {
        "user_id": user.id,
        "file_name": "file.txt",
        "attachment_type": AttachmentType.internal_use_only,
        "storage_key": storage_config.key,
    }


@pytest.fixture
def attachment(db, attachment_data):
    """Creates an attachment."""
    attachment = Attachment.create(db, data=attachment_data)
    yield attachment
    attachment.delete(db)


@pytest.fixture
def multiple_attachments(db, attachment_data, user):
    """Creates multiple attachments."""
    attachment_data["user_id"] = user.id
    attachment_data["file_name"] = "file_1.txt"
    attachment_1 = Attachment.create(db, data=attachment_data)

    attachment_data["file_name"] = "file_2.txt"
    attachment_2 = Attachment.create(db, data=attachment_data)

    attachment_data["file_name"] = "file_3.txt"
    attachment_3 = Attachment.create(db, data=attachment_data)

    yield attachment_1, attachment_2, attachment_3

    attachment_1.delete(db)
    attachment_2.delete(db)
    attachment_3.delete(db)


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
    attachment_reference.delete(db)
