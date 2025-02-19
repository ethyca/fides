import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fides.api.models.sql_models import Attachments, AttachmentReferences


@pytest.fixture
def attachment():
    return Attachments(
        id="1",
        user_id="user_1",
        file_name="file.txt",
        storage_url="http://example.com/file.txt",
        attachment_type="attach_to_dsr"
    )


@pytest.fixture
def attachment_reference(attachment):
    return AttachmentReferences(
        attachment_id=attachment.id,
        reference_id="ref_1",
        reference_type="manual_webhook"
    )


def attachment_setup(db: Session, attachment: Attachments, attachment_reference: AttachmentReferences):
    db.add(attachment)
    db.commit()
    db.add(attachment_reference)
    db.commit()


def test_create_attachment(db, attachment):
    """Test creating an attachment."""
    db.add(attachment)
    db.commit()
    retrieved_attachment = db.query(Attachments).filter_by(id=attachment.id).first()

    assert retrieved_attachment is not None
    assert retrieved_attachment.user_id == attachment.user_id
    assert retrieved_attachment.file_name == attachment.file_name
    assert retrieved_attachment.storage_url == attachment.storage_url
    assert retrieved_attachment.attachment_type == attachment.attachment_type


def test_create_attachment_reference(db, attachment, attachment_reference):
    """Test creating an attachment reference."""
    attachment_setup(db, attachment, attachment_reference)

    retrieved_reference = db.query(
        AttachmentReferences
    ).filter_by(reference_id=attachment_reference.reference_id).first()

    assert retrieved_reference is not None
    assert retrieved_reference.attachment_id == attachment_reference.attachment_id
    assert retrieved_reference.reference_type == attachment_reference.reference_type


def test_attachment_reference_relationship(db, attachment, attachment_reference):
    """Test the relationship between attachment and attachment reference."""
    attachment_setup(db, attachment, attachment_reference)

    retrieved_attachment = db.query(Attachments).filter_by(id="1").first()

    assert len(retrieved_attachment.references) == 1
    assert retrieved_attachment.references[0].reference_id == "ref_1"


def test_foreign_key_constraint(db):
    """Test that the foreign key constraint is enforced."""
    attachment_reference = AttachmentReferences(
        attachment_id="non_existent_id",
        reference_id="ref_1",
        reference_type="type_1"
    )
    db.add(attachment_reference)
    with pytest.raises(IntegrityError):
        db.commit()

def test_delete_attachment_cascades(db, attachment, attachment_reference):
    """Test that deleting an attachment cascades to its references."""
    attachment_setup(db, attachment, attachment_reference)

    db.delete(attachment)
    db.commit()

    retrieved_reference = db.query(AttachmentReferences).filter_by(reference_id="ref_1").first()
    assert retrieved_reference is None


@pytest.mark.parametrize(
    "attachment",
    [
        Attachments(
            id="1",
            user_id=None,
            file_name="file.txt",
            storage_url="http://example.com/file.txt",
            attachment_type="attach_to_dsr"
        ),
        Attachments(
            id="1",
            user_id="user_1",
            file_name=None,
            storage_url="http://example.com/file.txt",
             attachment_type="attach_to_dsr"
        ),
        Attachments(
            id="1",
            user_id="user_1",
            file_name="file.txt",
            storage_url=None,
            attachment_type="attach_to_dsr"
        )
    ]
)
def test_non_nullable_fields_attachments(db, attachment):
    """Test that non-nullable fields are enforced."""
    db.add(attachment)
    db.commit()
