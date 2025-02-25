from unittest.mock import patch

import boto3
import pytest

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.schemas.storage.storage import StorageDetails, StorageType
from moto import mock_aws
from unittest.mock import Mock


@pytest.fixture
def s3_client(storage_config):
    with mock_aws():
        session = boto3.Session(
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
            region_name="us-east-1",
        )
        s3 = session.client("s3")
        s3.create_bucket(Bucket=storage_config.details[StorageDetails.BUCKET.value])
        yield s3


@pytest.fixture(
    params=[
        ("testfile.pdf", b"%PDF-1.4 Test PDF content"),
        ("testfile.txt", b"Test text content"),
        ("testfile.jpeg", b"\xff\xd8\xff\xe0\x00\x10JFIF Test JPEG content"),
    ]
)
def attachment_file(request):
    file_name, file_content = request.param
    return file_name, file_content


@pytest.fixture
def attachment_data(user):
    return {
        "id": "1",
        "user_id": user.id,
        "file_name": "file.txt",
        "attachment_type": AttachmentType.internal_use_only,
    }


@pytest.fixture
def attachment(user, attachment_data):
    return Attachment(
        id=attachment_data["id"],
        user_id=user.id,
        file_name=attachment_data["file_name"],
        attachment_type=attachment_data["attachment_type"],
    )


@pytest.fixture
def attachment_reference(attachment):
    return AttachmentReference(
        attachment_id=attachment.id,
        reference_id="ref_1",
        reference_type=AttachmentReferenceType.privacy_request,
    )


def attachment_setup(
    db: Session, attachment: Attachment, attachment_reference: AttachmentReference
):
    db.add(attachment)
    db.commit()
    db.add(attachment_reference)
    db.commit()
    attachment.upload(db, b"Test content", "my_test_config_local")



def test_create_attachment_with_s3_storage(s3_client, db, attachment_data, attachment_file, storage_config, monkeypatch):
    """Test creating an attachment."""

    def mock_get_s3_client():
        return s3_client

    monkeypatch.setattr(
        "fides.api.models.attachment.get_s3_client", mock_get_s3_client
    )

    attachment = Attachment.create(db=db, data=attachment_data, attachment=attachment_file[1], storage_key=storage_config.key)
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()

    assert retrieved_attachment is not None
    assert retrieved_attachment.user_id == attachment.user_id
    assert retrieved_attachment.file_name == attachment.file_name
    assert retrieved_attachment.attachment_type == attachment.attachment_type

    assert s3_client.get_object(Bucket=storage_config.details[StorageDetails.BUCKET.value], Key=attachment.id) is not None
    assert retrieved_attachment.retrieve_attachment(db, storage_config.key) == attachment_file[1]
    assert "https://s3.amazonaws.com/test_bucket/1?AWSAccessKeyId=fake_access_key&" in retrieved_attachment.download_attachment_from_s3(db, storage_config.key)


def test_create_attachment_with_local_storage(db, attachment_data, attachment_file, storage_config_local):
    """Test creating an attachment."""
    attachment = Attachment.create(db=db, data=attachment_data, attachment=attachment_file[1], storage_key=storage_config_local.key)
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()

    assert retrieved_attachment is not None
    assert retrieved_attachment.user_id == attachment.user_id
    assert retrieved_attachment.file_name == attachment.file_name
    assert retrieved_attachment.attachment_type == attachment.attachment_type

    assert retrieved_attachment.retrieve_attachment(db, storage_config_local.key) == attachment_file[1]


def test_download_attachment_from_s3(
    s3_client, db, attachment, attachment_file, storage_config, monkeypatch
):
    """Test retrieving an attachment from S3."""

    def mock_get_s3_client():
        return s3_client

    monkeypatch.setattr(
        "fides.api.models.attachment.get_s3_client", mock_get_s3_client
    )
    attachment.file_name = attachment_file[0]
    attachment.upload(db, attachment_file[1], storage_config.key)

    # Retrieve the file using the method
    retrieved_file = attachment.download_attachment_from_s3(db, storage_config.key)
    assert "https://s3.amazonaws.com/test_bucket/1?AWSAccessKeyId=fake_access_key&" in retrieved_file


def test_retrieve_attachment_from_s3(s3_client, db, attachment, attachment_file, storage_config, monkeypatch):
    def mock_get_s3_client():
        return s3_client

    monkeypatch.setattr(
        "fides.api.models.attachment.get_s3_client", mock_get_s3_client
    )
    attachment.file_name = attachment_file[0]
    attachment.upload(db, attachment_file[1], storage_config.key)

    # Retrieve the file using the method
    retrieved_file = attachment.retrieve_attachment(db, storage_config.key)

    assert retrieved_file == attachment_file[1]


def test_retrieve_attachment_from_local(db, attachment, attachment_file, storage_config_local):
    """Test retrieving an attachment locally."""

    attachment.file_name = attachment_file[0]
    attachment.upload(db, attachment_file[1], storage_config_local.key)

    assert attachment.retrieve_attachment(db, storage_config_local.key) == attachment_file[1]



def test_delete_attachment_from_s3(
    s3_client, db, attachment, attachment_file, storage_config, monkeypatch
):
    """Test deleting an attachment from S3."""
    def mock_get_s3_client():
        return s3_client

    monkeypatch.setattr(
        "fides.api.models.attachment.get_s3_client", mock_get_s3_client
    )
    attachment.file_name = attachment_file[0]
    attachment.upload(db, attachment_file[1], storage_config.key)

    # Delete the file using the method
    attachment.delete_attachment_from_storage(db, storage_config.key)

    with pytest.raises(s3_client.exceptions.NoSuchKey):
        s3_client.get_object(Bucket=storage_config.details[StorageDetails.BUCKET.value], Key=attachment.id) is None


def test_delete_attachment_from_local(db, attachment, attachment_file, storage_config_local):
    """Test deleting an attachment locally."""

    attachment.file_name = attachment_file[0]
    attachment.upload(db, attachment_file[1], storage_config_local.key)

    # Delete the file using the method
    attachment.delete_attachment_from_storage(db, storage_config_local.key)

    with pytest.raises(FileNotFoundError):
        attachment.retrieve_attachment(db, storage_config_local.key)


def test_create_attachment_reference(db, attachment, attachment_reference, storage_config_local):
    """Test creating an attachment reference."""
    attachment_setup(db, attachment, attachment_reference)

    retrieved_reference = (
        db.query(AttachmentReference)
        .filter_by(reference_id=attachment_reference.reference_id)
        .first()
    )

    assert retrieved_reference is not None
    assert retrieved_reference.attachment_id == attachment_reference.attachment_id
    assert retrieved_reference.reference_type == attachment_reference.reference_type


def test_attachment_foreign_key_constraint(db):
    """Test that the foreign key constraint is enforced."""
    attachment = Attachment(
        id="2",
        user_id="non_existent_id",
        file_name="file.txt",
        attachment_type="attach_to_dsr",
    )
    db.add(attachment)
    with pytest.raises(IntegrityError):
        db.commit()


def test_attachment_reference_relationship(db, attachment, attachment_reference, storage_config_local):
    """Test the relationship between attachment and attachment reference."""
    attachment_setup(db, attachment, attachment_reference)

    retrieved_attachment = db.query(Attachment).filter_by(id="1").first()

    assert len(retrieved_attachment.references) == 1
    assert retrieved_attachment.references[0].reference_id == "ref_1"


def test_attachment_reference_foreign_key_constraint(db):
    """Test that the foreign key constraint is enforced."""
    attachment_reference = AttachmentReference(
        attachment_id="non_existent_id", reference_id="ref_1", reference_type="type_1"
    )
    db.add(attachment_reference)
    with pytest.raises(IntegrityError):
        db.commit()


def test_delete_attachment_cascades(db, attachment, attachment_reference, storage_config_local):
    """Test that deleting an attachment cascades to its references."""
    attachment_setup(db, attachment, attachment_reference)

    attachment.delete(db=db, storage_key=storage_config_local.key)

    retrieved_reference = (
        db.query(AttachmentReference).filter_by(reference_id="ref_1").first()
    )
    assert retrieved_reference is None


@pytest.mark.parametrize(
    "attachment_with_error",
    [
        Attachment(
            id="4",
            user_id=None,
            file_name="file.txt",
            attachment_type=AttachmentType.include_with_access_package,
        ),
        Attachment(
            id="5",
            user_id="user_1",
            file_name=None,
            attachment_type=AttachmentType.internal_use_only,
        ),
        Attachment(
            id="6",
            user_id="user_1",
            file_name="file.txt",
            attachment_type=None,
        ),
    ],
)
def test_non_nullable_fields_attachment(db, attachment_with_error):
    """Test that non-nullable fields are enforced."""
    db.add(attachment_with_error)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


@pytest.mark.parametrize(
    "attachment_reference_with_error",
    [
        AttachmentReference(
            attachment_id="attachment_1",
            reference_id=None,
            reference_type="type_1",
        ),
        AttachmentReference(
            attachment_id="attachment_1",
            reference_id="ref_1",
            reference_type=None,
        ),
    ],
)
def test_non_nullable_fields_attachment_references(db, attachment_reference_with_error):
    """Test that non-nullable fields are enforced."""
    db.add(attachment_reference_with_error)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_attachment_reference_unique_ids(db, attachment, attachment_reference, storage_config_local):
    """Test that the unique constraint on the attachment/reference id is enforced."""
    attachment_setup(db, attachment, attachment_reference)

    attachment_reference = AttachmentReference(
        attachment_id="attachment_1",
        reference_id="ref_1",
        reference_type=AttachmentReferenceType.privacy_request,
    )
    db.add(attachment_reference)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
