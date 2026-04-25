import pytest
from sqlalchemy.exc import IntegrityError

from fides.api.models.comment import Comment, CommentType
from fides.api.models.correspondence_metadata import (
    CorrespondenceDeliveryStatus,
    CorrespondenceMetadata,
)


@pytest.fixture
def correspondence_metadata(db, comment):
    metadata = CorrespondenceMetadata(
        comment_id=comment.id,
        message_id="test-msg-001@example.com",
        in_reply_to=None,
        reply_to_address="reply+abc@inbound.example.com",
        sender_email="privacy@example.com",
        recipient_email="subject@example.com",
    )
    db.add(metadata)
    db.commit()
    yield metadata
    # Cleanup handled by cascade if comment is deleted first,
    # otherwise delete explicitly
    if db.query(CorrespondenceMetadata).filter_by(id=metadata.id).first():
        db.delete(metadata)
        db.commit()


class TestCorrespondenceMetadata:
    """Tests for the CorrespondenceMetadata model.

    Validates the constraints that the TLA+ spec
    (CorrespondenceConcurrency.tla) relies on:
    - message_id UNIQUE for idempotency
    - comment_id UNIQUE for 1:1 relationship
    - CASCADE delete for PR deletion cleanup
    """

    def test_create_correspondence_metadata(self, db, correspondence_metadata, comment):
        """Test creating metadata and accessing it via the comment backref."""
        retrieved = (
            db.query(CorrespondenceMetadata)
            .filter_by(id=correspondence_metadata.id)
            .first()
        )
        assert retrieved is not None
        assert retrieved.comment_id == comment.id
        assert retrieved.message_id == "test-msg-001@example.com"
        assert retrieved.reply_to_address == "reply+abc@inbound.example.com"
        assert retrieved.sender_email == "privacy@example.com"
        assert retrieved.recipient_email == "subject@example.com"

        # Verify backref
        db.refresh(comment)
        assert comment.correspondence_metadata is not None
        assert comment.correspondence_metadata.id == correspondence_metadata.id

    def test_default_delivery_status_is_pending(self, db, correspondence_metadata):
        """Default delivery_status should be 'pending' per the FSM initial state."""
        assert (
            correspondence_metadata.delivery_status
            == CorrespondenceDeliveryStatus.pending
        )

    def test_message_id_unique_constraint(self, db, comment, correspondence_metadata):
        """Duplicate message_id must raise IntegrityError (idempotency guard)."""
        second_comment = Comment.create(
            db,
            data={
                "comment_text": "Second message",
                "comment_type": CommentType.message_to_subject,
            },
        )
        duplicate = CorrespondenceMetadata(
            comment_id=second_comment.id,
            message_id="test-msg-001@example.com",  # same as fixture
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.delete(second_comment)
        db.commit()

    def test_comment_id_unique_constraint(self, db, comment, correspondence_metadata):
        """Two metadata rows for the same comment must raise IntegrityError (1:1)."""
        duplicate = CorrespondenceMetadata(
            comment_id=comment.id,  # same comment as fixture
            message_id="different-msg-002@example.com",
        )
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_cascade_delete_removes_metadata(
        self, db, comment, correspondence_metadata
    ):
        """Deleting a comment must cascade-delete its CorrespondenceMetadata."""
        metadata_id = correspondence_metadata.id
        comment.delete(db)
        db.commit()

        assert (
            db.query(CorrespondenceMetadata).filter_by(id=metadata_id).first() is None
        )
