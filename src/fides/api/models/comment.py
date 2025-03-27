from enum import Enum as EnumType
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint, orm
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.attachment import Attachment, AttachmentReferenceType

if TYPE_CHECKING:
    from fides.api.models.attachment import AttachmentReference
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
        foreign_keys=[CommentReference.comment_id],
        primaryjoin=lambda: Comment.id == orm.foreign(CommentReference.comment_id),
    )

    def delete(self, db: Session) -> None:
        """Delete the comment and all associated references."""
        # Delete the comment
        Attachment.delete_attachments_for_reference_and_type(
            db, self.id, AttachmentReferenceType.comment
        )
        for reference in self.references:
            reference.delete(db)
        db.delete(self)

    @staticmethod
    def delete_comments_for_reference_and_type(
        db: Session, reference_id: str, reference_type: CommentReferenceType
    ) -> None:
        """
        Deletes comments associated with a given reference_id and reference_type.
        Delete all references to the comments.

        Args:
            db: Database session.
            reference_id: The reference id to delete.
            reference_type: The reference type to delete

        Examples:
          - Delete all comments associated with a privacy request.
            ``Comment.delete_comments_for_reference_and_type(
                db, privacy_request.id, CommentReferenceType.privacy_request
            )``
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
