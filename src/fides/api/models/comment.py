from enum import Enum as EnumType
from typing import Any

from sqlalchemy import Column
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.fides_user import FidesUser  # pylint: disable=unused-import


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
    Enum for attachment reference types. Indicates where attachment is referenced.
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
        backref="comments",
        lazy="selectin",
        uselist=False,
    )

    references = relationship(
        "CommentReference",
        back_populates="comment",
        cascade="all, delete",
        uselist=True,
    )

    def get_attachments(self, db: Session) -> list[Attachment]:
        """Retrieve all attachments associated with this comment."""
        stmt = (
            db.query(Attachment)
            .join(
                AttachmentReference, Attachment.id == AttachmentReference.attachment_id
            )
            .where(AttachmentReference.reference_id == self.id)
        )
        return db.execute(stmt).scalars().all()

    def delete(self, db: Session) -> None:
        """Delete the comment and all associated references."""
        attachments = self.get_attachments(db)
        for attachment in attachments:
            attachment.delete(db)
        db.delete(self)
        db.commit()
