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
from fides.api.models.privacy_request import PrivacyRequest


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
    assert retrieved_comment.comment_text == comment.comment_text
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
        comment_text="This is a note",
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


def test_comment_single_attachment_relationship(
    s3_client, db, comment, attachment, monkeypatch
):
    """Test the relationship between comment and a single attachment reference."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    attachment_reference = AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )
    db.refresh(comment)

    # Query attachment references directly
    attachment_refs = (
        db.query(AttachmentReference)
        .filter(
            AttachmentReference.reference_id == comment.id,
            AttachmentReference.reference_type == AttachmentReferenceType.comment,
        )
        .all()
    )

    assert len(attachment_refs) == 1
    assert attachment_refs[0].attachment_id == attachment.id
    assert attachment_refs[0].reference_id == comment.id
    assert attachment_refs[0].reference_type == AttachmentReferenceType.comment

    attachment_reference.delete(db=db)
    attachment.delete(db=db)


def test_comment_multiple_attachments_relationship(
    s3_client, db, comment, multiple_attachments, monkeypatch
):
    """Test the relationship between comment and multiple attachment references."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    # Create all references
    references = []
    for attachment in multiple_attachments:
        ref = AttachmentReference.create(
            db,
            data={
                "attachment_id": attachment.id,
                "reference_id": comment.id,
                "reference_type": AttachmentReferenceType.comment,
            },
        )
        references.append(ref)

    db.refresh(comment)

    # Query attachment references directly
    attachment_refs = (
        db.query(AttachmentReference)
        .filter(
            AttachmentReference.reference_id == comment.id,
            AttachmentReference.reference_type == AttachmentReferenceType.comment,
        )
        .all()
    )

    assert len(attachment_refs) == 3
    for i, ref in enumerate(attachment_refs):
        assert ref.attachment_id == multiple_attachments[i].id
        assert ref.reference_id == comment.id
        assert ref.reference_type == AttachmentReferenceType.comment

    # Cleanup
    for ref in references:
        ref.delete(db=db)
    for attachment in multiple_attachments:
        attachment.delete(db=db)


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


def test_delete_comment_cascades_to_attachments(
    s3_client, db, comment, attachment, monkeypatch
):
    """Test that deleting a comment cascades to its attachment references."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    attachment_reference = AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )
    db.refresh(comment)

    # Query attachment references directly
    attachment_refs = (
        db.query(AttachmentReference)
        .filter(
            AttachmentReference.reference_id == comment.id,
            AttachmentReference.reference_type == AttachmentReferenceType.comment,
        )
        .all()
    )
    assert len(attachment_refs) == 1

    comment_id = comment.id
    attachment_id = attachment.id
    comment.delete(db=db)
    db.commit()

    # Verify comment is deleted
    retrieved_comment = db.query(Comment).filter_by(id=comment_id).first()
    assert retrieved_comment is None

    # Verify attachment is deleted
    retrieved_attachment = db.query(Attachment).filter_by(id=attachment_id).first()
    assert retrieved_attachment is None

    # Verify reference is deleted
    retrieved_reference = (
        db.query(AttachmentReference).filter_by(id=attachment_reference.id).first()
    )
    assert retrieved_reference is None


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


def test_delete_all_comments(db, comment, privacy_request):
    """Test deleting all comments associated with a reference."""
    CommentReference.create(
        db,
        data={
            "comment_id": comment.id,
            "reference_id": privacy_request.id,
            "reference_type": CommentReferenceType.privacy_request,
        },
    )
    comment_id = comment.id
    Comment.delete_comments_for_reference_and_type(
        db, privacy_request.id, CommentReferenceType.privacy_request
    )
    db.commit()

    retrieved_comment = db.query(Comment).filter_by(id=comment_id).first()
    assert retrieved_comment is None

    retrieved_comment_reference = (
        db.query(CommentReference).filter_by(comment_id=comment_id).first()
    )
    assert retrieved_comment_reference is None


def test_relationship_warning_conditions(
    s3_client, db, comment, attachment, privacy_request, monkeypatch
):
    """Test the conditions that previously caused SQLAlchemy relationship warnings."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    # Create attachment reference for comment
    attachment_ref_1 = AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )
    db.refresh(comment)
    db.refresh(attachment)

    # Create attachment reference for privacy request
    attachment_ref_2 = AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": privacy_request.id,
            "reference_type": AttachmentReferenceType.privacy_request,
        },
    )
    db.refresh(privacy_request)
    db.refresh(attachment)

    # Create comment reference for privacy request
    comment_ref = CommentReference.create(
        db,
        data={
            "comment_id": comment.id,
            "reference_id": privacy_request.id,
            "reference_type": CommentReferenceType.privacy_request,
        },
    )
    db.refresh(comment)
    db.refresh(privacy_request)

    # Query attachment references directly
    comment_attachment_refs = (
        db.query(AttachmentReference)
        .filter(
            AttachmentReference.reference_id == comment.id,
            AttachmentReference.reference_type == AttachmentReferenceType.comment,
        )
        .all()
    )
    assert len(comment_attachment_refs) == 1
    assert comment_attachment_refs[0].attachment_id == attachment.id

    attachment_refs = attachment.references
    assert len(attachment_refs) == 2
    assert any(ref.reference_id == comment.id for ref in attachment_refs)
    assert any(ref.reference_id == privacy_request.id for ref in attachment_refs)

    # Cleanup - do this in reverse order of creation and check existence first
    if db.query(CommentReference).filter_by(id=comment_ref.id).first():
        comment_ref.delete(db)
        db.commit()

    if db.query(AttachmentReference).filter_by(id=attachment_ref_2.id).first():
        attachment_ref_2.delete(db)
        db.commit()

    if db.query(AttachmentReference).filter_by(id=attachment_ref_1.id).first():
        attachment_ref_1.delete(db)
        db.commit()

    # Refresh the session to ensure clean state
    db.expire_all()


def test_comment_attachment_relationship(
    s3_client, db, comment, attachment, monkeypatch
):
    """Test the relationship between a comment and its attachments."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    # Create attachment reference
    attachment_ref = AttachmentReference.create(
        db,
        data={
            "attachment_id": attachment.id,
            "reference_id": comment.id,
            "reference_type": AttachmentReferenceType.comment,
        },
    )
    db.refresh(comment)

    # Test the relationship
    assert len(comment.attachments) == 1
    assert comment.attachments[0] == attachment
    assert comment.attachments[0].file_name == attachment.file_name

    # Clean up
    attachment_ref.delete(db)
    attachment.delete(db)


def test_comment_multiple_attachments_relationship(
    s3_client, db, comment, multiple_attachments, monkeypatch
):
    """Test the relationship between a comment and multiple attachments."""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.api.tasks.storage.get_s3_client", mock_get_s3_client)

    # Create references for all attachments
    refs = []
    for attachment in multiple_attachments:
        ref = AttachmentReference.create(
            db,
            data={
                "attachment_id": attachment.id,
                "reference_id": comment.id,
                "reference_type": AttachmentReferenceType.comment,
            },
        )
        refs.append(ref)

    db.refresh(comment)

    # Test the relationships
    assert len(comment.attachments) == len(multiple_attachments)
    for attachment in multiple_attachments:
        assert attachment in comment.attachments

    # Clean up
    for ref in refs:
        ref.delete(db)
    for attachment in multiple_attachments:
        attachment.delete(db)
