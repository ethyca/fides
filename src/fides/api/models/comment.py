from enum import Enum as EnumType
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.attachment import AttachmentReferenceType, delete_all_attachments

if TYPE_CHECKING:
    from fides.api.models.attachment import Attachment, AttachmentReference
    from fides.api.models.fides_user import FidesUser
    from fides.api.models.privacy_request import PrivacyRequest


class CommentType(str, EnumType):
    """
    Enum for comment types. Indicates comment usage.

    - notes are internal comments.
    - reply comments are public and may cause an email or other communciation to be sent
    """

    note = "note"
    reply = "reply"


class CommentReferenceType(str, EnumType):
    """
    Enum for comment reference types. Indicates where the comment is referenced.
    """

    manual_step = "manual_step"
    privacy_request = "privacy_request"


class CommentReference(Base):
    """
    Stores information about a comment and any other element which may reference that comment.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "comment_reference"

    comment_id = Column(String, ForeignKey("comment.id"), nullable=False)
    reference_id = Column(String, nullable=False)
    reference_type = Column(EnumColumn(CommentReferenceType), nullable=False)

    __table_args__ = (
        UniqueConstraint("comment_id", "reference_id", name="comment_reference_uc"),
    )

    comment = relationship(
        "Comment",
        back_populates="references",
        uselist=False,
    )

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = False
    ) -> "CommentReference":
        """Creates a new comment reference record in the database."""
        return super().create(db=db, data=data, check_name=check_name)


class Comment(Base):
    """
    Stores information about a Comment.
    """

    user_id = Column(
        String, ForeignKey("fidesuser.id", ondelete="SET NULL"), nullable=True
    )
    comment_text = Column(String, nullable=False)
    comment_type = Column(EnumColumn(CommentType), nullable=False)

    user = relationship(
        "FidesUser",
        lazy="selectin",
        uselist=False,
    )

    references = relationship(
        "CommentReference",
        back_populates="comment",
        cascade="all, delete-orphan",
        uselist=True,
    )

    attachments = relationship(
        "Attachment",
        secondary="attachment_reference",
        primaryjoin="and_(Comment.id == AttachmentReference.reference_id, "
        "AttachmentReference.reference_type == 'comment')",
        secondaryjoin="Attachment.id == AttachmentReference.attachment_id",
        order_by="Attachment.created_at",
        back_populates="comments",
    )

    privacy_requests = relationship(
        "PrivacyRequest",
        secondary="comment_reference",
        primaryjoin="and_(Comment.id == CommentReference.comment_id, "
        "CommentReference.reference_type == 'privacy_request')",
        secondaryjoin="PrivacyRequest.id == CommentReference.reference_id",
        back_populates="comments",
    )

    def delete(self, db: Session) -> None:
        """Delete the comment and all associated references."""
        # Delete the comment
        delete_all_attachments(db, self.id, AttachmentReferenceType.comment)
        for reference in self.references:
            reference.delete(db)
        db.delete(self)


def delete_all_comments(
    db: Session, reference_id: str, reference_type: CommentReferenceType
) -> None:
    """
    Deletes comments associated with this reference_id and reference_type.
    Delete all references to the comments.
    """
    # Query comments explicitly to avoid lazy loading
    comments = (
        db.query(Comment)
        .join(CommentReference)
        .filter(
            CommentReference.reference_id == reference_id,
            CommentReference.reference_type == reference_type,
        )
        .all()
    )

    for comment in comments:
        comment.delete(db)
