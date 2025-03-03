import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.models.attachment import (
    Attachment,
    AttachmentReference,
    AttachmentReferenceType,
)
from fides.api.models.comment import (
    Comment,
    CommentReference,
    CommentReferenceType,
    CommentType,
)
from fides.api.models.fides_user import FidesUser


@pytest.fixture
def comment_data(user):
    return {
        "user_id": user.id,
        "note_text": "This is a note",
        "comment_type": CommentType.note,
    }


@pytest.fixture
def comment(db, comment_data):
    comment = Comment.create(db, data=comment_data)
    yield comment
    comment.delete(db)


@pytest.fixture
def comment_reference(db, comment):
    comment_reference = CommentReference.create(
        db=db,
        data={
            "comment_id": comment.id,
            "reference_id": "ref_1",
            "reference_type": CommentReferenceType.privacy_request,
        },
    )
    yield comment_reference
    comment_reference.delete(db)


def test_create_comment(db, comment_data, user):
    """Test creating a comment."""
    comment = Comment.create(db=db, data=comment_data)
    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()

    assert retrieved_comment is not None
    assert retrieved_comment.user_id == comment.user_id
    assert retrieved_comment.note_text == comment.note_text
    assert retrieved_comment.comment_type == comment.comment_type

    assert comment.user.id == user.id
    assert comment.user.first_name == user.first_name


def test_create_comment_reference(db, comment_reference):
    """Test creating a comment reference."""

    retrieved_reference = (
        db.query(CommentReference)
        .filter_by(reference_id=comment_reference.reference_id)
        .first()
    )

    assert retrieved_reference is not None
    assert retrieved_reference.comment_id == comment_reference.comment_id
    assert retrieved_reference.reference_type == comment_reference.reference_type


def test_comment_foreign_key_constraint(db):
    """Test that the foreign key constraint is enforced."""
    comment = Comment(
        user_id="non_existent_id",
        note_text="This is a note",
        comment_type="note",
    )
    db.add(comment)
    with pytest.raises(IntegrityError):
        db.commit()


def test_comment_fidesuser_foreign_key_constraint(db, comment):
    """Test that user can be deleted without deleting the comment."""
    db.add(comment)
    db.commit()

    user = db.query(FidesUser).filter_by(id=comment.user_id).first()
    db.delete(user)
    db.commit()

    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()
    assert retrieved_comment is not None


def test_comment_reference_relationship(db, comment, comment_reference):
    """Test the relationship between comment and comment reference."""

    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()

    assert len(retrieved_comment.references) == 1
    assert (
        retrieved_comment.references[0].reference_id == comment_reference.reference_id
    )


def test_comment_single_attachment_relationship(db, comment, attachment):
    """Test the relationship between comment and attachment."""

    attachment_reference = AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )

    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()

    attachments = retrieved_comment.get_attachments(db)

    assert len(attachments) == 1
    assert attachments[0].id == attachment.id
    assert (
        attachments[0].references[0].reference_id == attachment_reference.reference_id
    )
    assert (
        attachments[0].references[0].reference_type
        == attachment_reference.reference_type
    )


def test_comment_multiple_attachments_relationship(db, comment, multiple_attachments):
    """Test the relationship between comment and multiple attachments."""

    attachment_reference_1 = AttachmentReference.create(
        db,
        data={
            "attachment_id": multiple_attachments[0].id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )
    attachment_reference_2 = AttachmentReference.create(
        db,
        data={
            "attachment_id": multiple_attachments[1].id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )
    attachment_reference_3 = AttachmentReference.create(
        db,
        data={
            "attachment_id": multiple_attachments[2].id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )

    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()

    attachments = retrieved_comment.get_attachments(db)
    assert len(attachments) == 3
    assert attachments[0].id == multiple_attachments[0].id
    assert (
        attachments[0].references[0].reference_id == attachment_reference_1.reference_id
    )
    assert (
        attachments[0].references[0].reference_type
        == attachment_reference_1.reference_type
    )
    assert attachments[1].id == multiple_attachments[1].id
    assert (
        attachments[1].references[0].reference_id == attachment_reference_2.reference_id
    )
    assert (
        attachments[1].references[0].reference_type
        == attachment_reference_2.reference_type
    )
    assert attachments[2].id == multiple_attachments[2].id
    assert (
        attachments[2].references[0].reference_id == attachment_reference_3.reference_id
    )
    assert (
        attachments[2].references[0].reference_type
        == attachment_reference_3.reference_type
    )


def test_delete_comment_cascades(db, comment, comment_reference):
    """Test that deleting a comment cascades to its references."""
    retrieved_reference = (
        db.query(CommentReference)
        .filter_by(reference_id=comment_reference.reference_id)
        .first()
    )
    assert retrieved_reference is not None

    comment.delete(db=db)

    retrieved_reference = (
        db.query(CommentReference)
        .filter_by(reference_id=comment_reference.reference_id)
        .first()
    )
    assert retrieved_reference is None


def test_delete_comment_cascades_to_attachments(db, comment, attachment):
    """Test that deleting a comment cascades to its attachments."""
    attachment_reference = AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )

    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()
    attachments = retrieved_comment.get_attachments(db)
    assert len(attachments) == 1

    comment.delete(db=db)

    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()
    assert retrieved_comment is None

    retrieved_attachment = db.query(Attachment).filter_by(id=attachment.id).first()
    assert retrieved_attachment is None

    retrieved_attachment_reference = (
        db.query(AttachmentReference)
        .filter_by(reference_id=attachment_reference.reference_id)
        .first()
    )
    assert retrieved_attachment_reference is None


def test_comment_reference_foreign_key_constraint(db):
    """Test that the foreign key constraint is enforced."""
    comment_reference = CommentReference(
        comment_id="non_existent_id",
        reference_id="ref_1",
        reference_type=CommentReferenceType.privacy_request,
    )
    db.add(comment_reference)
    with pytest.raises(IntegrityError):
        db.commit()


def test_delete_comment_reference_cascades(db, comment, comment_reference):
    """Test that deleting a comment reference does not delete the comment."""
    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()
    assert retrieved_comment is not None

    comment_reference.delete(db=db)

    retrieved_comment = db.query(Comment).filter_by(id=comment.id).first()
    assert retrieved_comment is not None
    assert len(retrieved_comment.references) == 0
