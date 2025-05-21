import warnings
from io import BytesIO
from tempfile import SpooledTemporaryFile
from unittest.mock import create_autospec

import boto3
import google.auth.credentials
import google.oauth2.service_account
import pytest
import requests
from botocore.exceptions import ClientError
from google.cloud import storage
from google.cloud.exceptions import NotFound
from moto import mock_aws
from sqlalchemy import exc as sa_exc
from sqlalchemy.exc import IntegrityError

from fides.api.common_exceptions import StorageUploadError
from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)
from fides.api.models.fides_user import FidesUser
from fides.api.models.storage import StorageConfig
from fides.api.schemas.storage.storage import StorageDetails
from fides.api.service.storage.gcs import GCSAuthMethod
from fides.api.service.storage.util import get_local_filename


@pytest.fixture(
    params=[
        ("testfile.pdf", b"%PDF-1.4 Test PDF content"),
        ("testfile.txt", b"Test text content"),
        ("testfile.jpeg", b"\xff\xd8\xff\xe0\x00\x10JFIF Test JPEG content"),
    ],
    scope="function",
)
def attachment_file(request):
    """
    Fixture to provide file-like objects for testing.
    Each parameter is a tuple of (filename, file content as bytes).
    A new BytesIO object is created for each test to avoid reuse issues.
    """
    filename, file_content = request.param
    attachment_file = SpooledTemporaryFile(max_size=1024, mode="w+b")
    attachment_file.write(file_content)
    attachment_file.seek(0)  # Reset the file pointer
    return filename, attachment_file


def verify_attachment_created_uploaded_s3(attachment, attachment_file_copy):
    retrieved_file_size, download_url = attachment.retrieve_attachment()
    assert retrieved_file_size == len(attachment_file_copy)
    assert attachment.config.details[StorageDetails.BUCKET.value] in download_url
    assert f"{attachment.id}/{attachment.file_name}" in download_url


def verify_attachment_created_uploaded_local(attachment, attachment_file_copy):
    retrieved_attachment_size, download_path = attachment.retrieve_attachment()
    assert retrieved_attachment_size == len(attachment_file_copy)
    assert download_path == get_local_filename(
        f"{attachment.id}/{attachment.file_name}"
    )


def verify_attachment_created_uploaded_gcs(attachment, attachment_file_copy):
    """Verify that an attachment was created and uploaded to GCS correctly."""
    retrieved_file_size, download_url = attachment.retrieve_attachment()
    assert retrieved_file_size == len(attachment_file_copy)
    assert attachment.config.details[StorageDetails.BUCKET.value] in download_url
    assert f"{attachment.id}/{attachment.file_name}" in download_url


@pytest.fixture
def mock_gcs_client(
    base_gcs_client_mock, monkeypatch, storage_config_default_gcs, attachment_file
):
    """Fixture to provide mocked GCS client for attachment tests."""
    # Get the file content for size calculation
    file_content = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset file pointer

    # Mock blob methods
    def mock_upload_from_file(*args, **kwargs):
        return None

    def mock_upload_from_filename(*args, **kwargs):
        return None

    def mock_upload_from_string(*args, **kwargs):
        return None

    def mock_generate_signed_url(*args, **kwargs):
        # Get the blob name from the first argument (self)
        blob_name = args[0].name if args else "test_file.txt"
        bucket_name = storage_config_default_gcs.details[StorageDetails.BUCKET.value]
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    # Mock blob size property
    def mock_size(self):
        return len(file_content)

    monkeypatch.setattr(
        "google.cloud.storage.Blob.upload_from_file", mock_upload_from_file
    )
    monkeypatch.setattr(
        "google.cloud.storage.Blob.upload_from_filename", mock_upload_from_filename
    )
    monkeypatch.setattr(
        "google.cloud.storage.Blob.upload_from_string", mock_upload_from_string
    )
    monkeypatch.setattr(
        "google.cloud.storage.Blob.generate_signed_url", mock_generate_signed_url
    )
    monkeypatch.setattr("google.cloud.storage.Blob.size", property(mock_size))

    return base_gcs_client_mock


def test_create_attachment_without_attachement_file_raises_error(db, attachment_data):
    """Test creating an attachment without an attachment file raises an error."""
    with mock_aws():
        with pytest.raises(ClientError) as excinfo:
            Attachment.create_and_upload(db, data=attachment_data, attachment_file=None)
            assert (
                "Failed to upload attachment: The 'document' parameter must be a file-like object"
                in str(excinfo.value)
            )


def test_create_attachment_with_S3_storage(
    s3_client, db, user, attachment_data, attachment_file, monkeypatch
):
    """Test creating an attachment."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test

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
            Key=f"{attachment.id}/{attachment.file_name}",
        )
        is not None
    )
    verify_attachment_created_uploaded_s3(attachment, attachment_file_copy)
    attachment.delete(db)


def test_create_attachment_with_local_storage(
    db, attachment_data, attachment_file, storage_config_local
):
    """Test creating an attachment."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test

    attachment_data["storage_key"] = storage_config_local.key
    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()

    assert retrieved_attachment is not None
    assert retrieved_attachment.user_id == attachment.user_id
    assert retrieved_attachment.file_name == attachment.file_name
    assert retrieved_attachment.attachment_type == attachment.attachment_type

    verify_attachment_created_uploaded_local(attachment, attachment_file_copy)
    attachment.delete(db)


def test_create_attachment_with_GCS_storage(
    mock_gcs_client,
    db,
    user,
    attachment_data,
    attachment_file,
    storage_config_default_gcs,
):
    """Test creating an attachment with GCS storage."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test

    # Update attachment data to use GCS storage config
    attachment_data["storage_key"] = storage_config_default_gcs.key

    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )
    verify_attachment_created_uploaded_gcs(attachment, attachment_file_copy)
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
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    attachment = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=attachment_file[1]
    )
    verify_attachment_created_uploaded_s3(attachment, attachment_file_copy)
    attachment.delete(db)


def test_retrieve_attachment_from_local(
    db, attachment_data, attachment_file, storage_config_local
):
    """Test retrieving an attachment locally."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test
    attachment_data["storage_key"] = storage_config_local.key
    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )

    verify_attachment_created_uploaded_local(attachment, attachment_file_copy)
    attachment.delete(db)


def test_retrieve_attachment_from_gcs(
    mock_gcs_client, db, attachment_data, attachment_file, storage_config_default_gcs
):
    """Test retrieving an attachment from GCS storage."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test

    # Update attachment data to use GCS storage config
    attachment_data["storage_key"] = storage_config_default_gcs.key

    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )
    verify_attachment_created_uploaded_gcs(attachment, attachment_file_copy)
    attachment.delete(db)


def test_delete_attachment_from_s3(
    s3_client, db, attachment_data, attachment_file, monkeypatch
):
    """Test deleting an attachment from S3."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    attachment = Attachment.create_and_upload(
        db, data=attachment_data, attachment_file=attachment_file[1]
    )
    verify_attachment_created_uploaded_s3(attachment, attachment_file_copy)

    # Delete the file using the method
    attachment.delete_attachment_from_storage()

    with pytest.raises(s3_client.exceptions.NoSuchKey):
        s3_client.get_object(
            Bucket=attachment.config.details[StorageDetails.BUCKET.value],
            Key=f"{attachment.id}/{attachment.file_name}",
        ) is None
    attachment.delete(db)


def test_delete_attachment_from_local(
    db, attachment_data, attachment_file, storage_config_local
):
    """Test deleting an attachment locally."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test
    attachment_data["storage_key"] = storage_config_local.key
    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )
    verify_attachment_created_uploaded_local(attachment, attachment_file_copy)

    # Delete the file using the method
    attachment.delete_attachment_from_storage()

    with pytest.raises(FileNotFoundError):
        attachment.retrieve_attachment()
    db.delete(attachment)


def test_delete_attachment_from_gcs(
    mock_gcs_client, db, attachment_data, attachment_file, storage_config_default_gcs
):
    """Test deleting an attachment from GCS storage."""
    # Create a copy of the file content for verification
    attachment_file_copy = attachment_file[1].read()
    attachment_file[1].seek(0)  # Reset the file pointer again for the test

    # Update attachment data to use GCS storage config
    attachment_data["storage_key"] = storage_config_default_gcs.key

    attachment = Attachment.create_and_upload(
        db=db, data=attachment_data, attachment_file=attachment_file[1]
    )
    verify_attachment_created_uploaded_gcs(attachment, attachment_file_copy)
    attachment.delete(db)


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
        db=db, data=attachment_data, attachment_file=BytesIO(b"test file content")
    )
    attachment_id = attachment.id

    config = db.query(StorageConfig).filter_by(key=attachment.storage_key).first()
    config.delete(db)

    retrieved_attachment = db.query(Attachment).filter_by(id=attachment_id).first()
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


def test_delete_all_attachments(db, attachment, comment, privacy_request):
    """Tests delete_all_attachments_for_reference_and_type function."""
    # create attachment references to comment and privacy request
    AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": privacy_request.id,
            "reference_type": AttachmentReferenceType.privacy_request,
        },
    )
    AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )

    # delete all attachments associated with the comment
    # should delete all attachments and references to the attachment
    Attachment.delete_attachments_for_reference_and_type(
        db, reference_id=comment.id, reference_type=AttachmentReferenceType.comment
    )
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()
    assert retrieved_attachment is None

    # verify the reference to the "deleted" comment is removed
    retrieved_comment_reference = (
        db.query(AttachmentReference).filter_by(reference_id=comment.id).first()
    )
    assert retrieved_comment_reference is None

    # verify the attachment and reference to the privacy request is also removed
    retrieved_pr_reference = (
        db.query(AttachmentReference).filter_by(reference_id=privacy_request.id).first()
    )
    assert retrieved_pr_reference is None


def test_attachment_relationship_warnings(
    s3_client, db, attachment, comment, privacy_request, monkeypatch
):
    """Test that no SQLAlchemy relationship warnings occur when creating and accessing Attachment relationships."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Create references to both comment and privacy request
        attachment_ref_1 = AttachmentReference.create(
            db,
            data={
                "attachment_id": attachment.id,
                "reference_id": comment.id,
                "reference_type": AttachmentReferenceType.comment,
            },
        )
        db.refresh(attachment)
        db.refresh(comment)

        attachment_ref_2 = AttachmentReference.create(
            db,
            data={
                "attachment_id": attachment.id,
                "reference_id": privacy_request.id,
                "reference_type": AttachmentReferenceType.privacy_request,
            },
        )
        db.refresh(attachment)
        db.refresh(privacy_request)

        # Test accessing relationships in various ways
        assert len(attachment.references) == 2

        # Query references directly
        refs = (
            db.query(AttachmentReference)
            .filter(AttachmentReference.attachment_id == attachment.id)
            .all()
        )
        assert len(refs) == 2
        assert any(
            ref.reference_type == AttachmentReferenceType.comment for ref in refs
        )
        assert any(
            ref.reference_type == AttachmentReferenceType.privacy_request
            for ref in refs
        )

        # Verify no SQLAlchemy relationship warnings were emitted
        sqlalchemy_warnings = [
            w for w in warning_list if issubclass(w.category, sa_exc.SAWarning)
        ]
        assert (
            len(sqlalchemy_warnings) == 0
        ), f"SQLAlchemy warnings found: {[str(w.message) for w in sqlalchemy_warnings]}"

        # Cleanup
        if db.query(AttachmentReference).filter_by(id=attachment_ref_2.id).first():
            attachment_ref_2.delete(db)
            db.commit()

        if db.query(AttachmentReference).filter_by(id=attachment_ref_1.id).first():
            attachment_ref_1.delete(db)
            db.commit()

        # Refresh the session to ensure clean state
        db.expire_all()
