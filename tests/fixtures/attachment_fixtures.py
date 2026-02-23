from io import BytesIO

import pytest
from sqlalchemy.orm import Session

from fides.api.models.attachment import AttachmentType
from fides.api.models.comment import Comment, CommentType
from fides.service.attachment.attachment_service import AttachmentService


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

    monkeypatch.setattr("fides.service.storage.s3.get_s3_client", mock_get_s3_client)
    attachment = AttachmentService(db).create_and_upload(
        data=attachment_data, file_data=BytesIO(b"file content")
    )
    yield attachment
    AttachmentService(db).delete(attachment)


@pytest.fixture
def attachment_include_in_download(s3_client, db, attachment_data, monkeypatch):
    """Creates an attachment that is included in the download."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.service.storage.s3.get_s3_client", mock_get_s3_client)
    attachment_data["attachment_type"] = AttachmentType.include_with_access_package
    attachment = AttachmentService(db).create_and_upload(
        data=attachment_data, file_data=BytesIO(b"file content")
    )
    yield attachment
    AttachmentService(db).delete(attachment)


@pytest.fixture(scope="function")
def attachment_file():
    """Returns a test file for attachment upload tests."""
    content = b"test file content for attachment"
    return ("test_attachment.txt", BytesIO(content), "text/plain")


@pytest.fixture(scope="function")
def comment_data(user):
    return {
        "user_id": user.id,
        "comment_text": "This is a note",
        "comment_type": CommentType.note,
    }


@pytest.fixture(scope="function")
def comment(db, comment_data):
    comment = Comment.create(db, data=comment_data)
    yield comment
    comment.delete(db)
