import pytest

from sqlalchemy.orm.exc import StaleDataError
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.schemas.storage.storage import StorageDetails


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
def attachment(s3_client, db, attachment_data, monkeypatch):
    """Creates an attachment."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.service.storage.s3.get_s3_client", mock_get_s3_client)
    attachment = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=b"file content"
    )
    yield attachment
    try:
        attachment.delete(db)
    except Exception:
        pass


@pytest.fixture
def multiple_attachments(s3_client, db, attachment_data, user, monkeypatch):
    """Creates multiple attachments."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.service.storage.s3.get_s3_client", mock_get_s3_client)

    attachment_data["user_id"] = user.id
    attachment_data["file_name"] = "file_1.txt"
    attachment_1 = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=b"file content 1"
    )

    attachment_data["file_name"] = "file_2.txt"
    attachment_2 = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=b"file content 2"
    )

    attachment_data["file_name"] = "file_3.txt"
    attachment_3 = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=b"file content 3"
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
    attachment_reference.delete(db)
