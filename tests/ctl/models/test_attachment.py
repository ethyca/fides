from unittest.mock import Mock, patch

import boto3
import pytest
from moto import mock_aws
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.fides_user import FidesUser
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import StorageDetails


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
def attachment_data(user, storage_config):
    return {
        "user_id": user.id,
        "file_name": "file.txt",
        "attachment_type": AttachmentType.internal_use_only,
        "storage_key": storage_config.key,
    }


@pytest.fixture(scope="function")
def attachment(db, attachment_data, monkeypatch, s3_client):
    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)
    attachment = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=b"test file content"
    )
    yield attachment
    attachment.delete(db)


@pytest.fixture
def attachment_reference(db, attachment):
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


def test_create_attachment_without_attachement_file_raises_error(db, attachment_data):
    """Test creating an attachment without an attachment file raises an error."""
    with pytest.raises(ValueError):
        Attachment.create_and_upload(db, data=attachment_data, attachment_file=None)


def test_create_attachment_with_S3_storage(
    s3_client, db, user, attachment_data, attachment_file, monkeypatch
):
    """Test creating an attachment."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    attachment = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=attachment_file[1]
    )
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()

    assert retrieved_attachment is not None
    assert retrieved_attachment.user_id == attachment.user_id
    assert retrieved_attachment.file_name == attachment.file_name
    assert retrieved_attachment.attachment_type == attachment.attachment_type

    assert attachment.user.id == user.id
    assert attachment.user.first_name == user.first_name
    assert (
        s3_client.get_object(
            Bucket=attachment.config.details[StorageDetails.BUCKET.value],
            Key=attachment.id,
        )
        is not None
    )
    assert retrieved_attachment.retrieve_attachment() == attachment_file[1]
    attachment.delete(db)


def test_create_attachment_with_local_storage(
    db, attachment_data, attachment_file, storage_config_local
):
    """Test creating an attachment."""

    attachment_data["storage_key"] = storage_config_local.key
    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()

    assert retrieved_attachment is not None
    assert retrieved_attachment.user_id == attachment.user_id
    assert retrieved_attachment.file_name == attachment.file_name
    assert retrieved_attachment.attachment_type == attachment.attachment_type

    assert retrieved_attachment.retrieve_attachment() == attachment_file[1]
    attachment.delete(db)


def test_create_attachment_reference(db, attachment_reference):
    """Test creating an attachment reference."""

    retrieved_reference = (
        db.query(AttachmentReference)
        .filter_by(reference_id=attachment_reference.reference_id)
        .first()
    )

    assert retrieved_reference is not None
    assert retrieved_reference.attachment_id == attachment_reference.attachment_id
    assert retrieved_reference.reference_type == attachment_reference.reference_type


def test_retrieve_attachment_from_s3(
    s3_client, db, attachment_data, attachment_file, monkeypatch
):
    """Test retrieving an attachment (bytes) from S3."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    attachment = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=attachment_file[1]
    )
    retrieved_file = attachment.retrieve_attachment()
    assert retrieved_file == attachment_file[1]
    attachment.delete(db)


def test_retrieve_attachment_from_local(
    db, attachment_data, attachment_file, storage_config_local
):
    """Test retrieving an attachment locally."""

    attachment_data["storage_key"] = storage_config_local.key
    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )

    assert attachment.retrieve_attachment() == attachment_file[1]
    attachment.delete(db)


def test_delete_attachment_from_s3(
    s3_client, db, attachment_data, attachment_file, monkeypatch
):
    """Test deleting an attachment from S3."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    attachment = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=attachment_file[1]
    )

    assert attachment.retrieve_attachment() == attachment_file[1]

    # Delete the file using the method
    attachment.delete_attachment_from_storage()

    with pytest.raises(s3_client.exceptions.NoSuchKey):
        s3_client.get_object(
            Bucket=attachment.config.details[StorageDetails.BUCKET.value],
            Key=attachment.id,
        ) is None
    attachment.delete(db)


def test_delete_attachment_from_local(
    db, attachment_data, attachment_file, storage_config_local
):
    """Test deleting an attachment locally."""
    attachment_data["storage_key"] = storage_config_local.key
    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )

    assert attachment.retrieve_attachment() == attachment_file[1]

    # Delete the file using the method
    attachment.delete_attachment_from_storage()

    with pytest.raises(FileNotFoundError):
        attachment.retrieve_attachment()
    db.delete(attachment)


def test_attachment_fidesuser_foreign_key_constraint(db, attachment):
    """Test that user can be deleted without deleting the attachment."""
    db.add(attachment)
    db.commit()

    user = db.query(FidesUser).filter_by(id=attachment.user_id).first()
    db.delete(user)
    db.commit()

    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()
    assert retrieved_attachment is not None


def test_attachment_storageconfig_foreign_key_constraint(
    db, attachment_data, storage_config_local
):
    """Test that deleting storage config cascades."""
    attachment_data["storage_key"] = storage_config_local.key
    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=b"test file content"
    )

    config = db.query(StorageConfig).filter_by(key=attachment.storage_key).first()
    config.delete(db)

    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()
    assert retrieved_attachment is None


def test_attachment_reference_relationship(db, attachment, attachment_reference):
    """Test the relationship between attachment and attachment reference."""

    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()

    assert len(retrieved_attachment.references) == 1
    assert (
        retrieved_attachment.references[0].reference_id
        == attachment_reference.reference_id
    )


def test_attachment_reference_foreign_key_constraint(db):
    """Test that the foreign key constraint is enforced."""
    attachment_reference = AttachmentReference(
        attachment_id="non_existent_id", reference_id="ref_1", reference_type="type_1"
    )
    db.add(attachment_reference)
    with pytest.raises(IntegrityError):
        db.commit()


def test_delete_attachment_cascades(db, attachment, attachment_reference):
    """Test that deleting an attachment cascades to its references."""
    retrieved_reference = (
        db.query(AttachmentReference)
        .filter_by(reference_id=attachment_reference.reference_id)
        .first()
    )
    assert retrieved_reference is not None

    attachment.delete(db)

    retrieved_reference = (
        db.query(AttachmentReference)
        .filter_by(reference_id=attachment_reference.reference_id)
        .first()
    )
    assert retrieved_reference is None


@pytest.mark.parametrize(
    "attachment_with_error",
    [
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


def test_attachment_reference_unique_ids(db, attachment_reference):
    """Test that the unique constraint on the attachment/reference id is enforced."""

    attachment_reference = AttachmentReference(
        attachment_id="attachment_1",
        reference_id="ref_1",
        reference_type=AttachmentReferenceType.privacy_request,
    )
    db.add(attachment_reference)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
