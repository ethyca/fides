import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.sql_models import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
    AttachmentType,
)


@pytest.fixture
def attachment(user):
    return Attachment(
        id="1",
        user_id=user.id,
        file_name="file.txt",
        storage_url="http://example.com/file.txt",
        attachment_type=AttachmentType.internal_use_only,
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


def test_create_attachment(db, attachment):
    """Test creating an attachment."""
    db.add(attachment)
    db.commit()
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()

    assert retrieved_attachment is not None
    assert retrieved_attachment.user_id == attachment.user_id
    assert retrieved_attachment.file_name == attachment.file_name
    assert retrieved_attachment.storage_url == attachment.storage_url
    assert retrieved_attachment.attachment_type == attachment.attachment_type


def test_create_attachment_reference(db, attachment, attachment_reference):
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
        storage_url="http://example.com/file.txt",
        attachment_type="attach_to_dsr",
    )
    db.add(attachment)
    with pytest.raises(IntegrityError):
        db.commit()


def test_attachment_reference_relationship(db, attachment, attachment_reference):
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


def test_delete_attachment_cascades(db, attachment, attachment_reference):
    """Test that deleting an attachment cascades to its references."""
    attachment_setup(db, attachment, attachment_reference)

    db.delete(attachment)
    db.commit()

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
            storage_url="http://example.com/file.txt",
            attachment_type="attach_to_dsr",
        ),
        Attachment(
            id="5",
            user_id="user_1",
            file_name=None,
            storage_url="http://example.com/file.txt",
            attachment_type="attach_to_dsr",
        ),
        Attachment(
            id="6",
            user_id="user_1",
            file_name="file.txt",
            storage_url=None,
            attachment_type="attach_to_dsr",
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
