from enum import Enum as EnumType
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, func, orm
from sqlalchemy import Enum as EnumColumn
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base, FidesBase
from fides.api.models.attachment import AttachmentReferenceType
from fides.service.attachment_service import AttachmentService

if TYPE_CHECKING:
    from fides.api.models.attachment import Attachment, AttachmentReference
    from fides.api.models.fides_user import FidesUser
    from fides.api.models.privacy_request import PrivacyRequest


class CommentType(str, EnumType):
    """
    Enum for comment types. Indicates comment usage.

    - notes are internal comments.
    - reply is reserved for future use and is not currently supported
    """

    note = "note"
    reply = "reply"


class CommentReferenceType(str, EnumType):
    """
    Enum for comment reference types. Indicates where the comment is referenced.
    """

    access_manual_webhook = "access_manual_webhook"
    erasure_manual_webhook = "erasure_manual_webhook"
    privacy_request = "privacy_request"
    manual_task_submission = "manual_task_submission"


class CommentReference(Base):
    """
    Stores information about a comment and any other element which may reference that comment.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "comment_reference"

    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    comment_id = Column(
        String,
        ForeignKey(
            "comment.id", name="comment_reference_comment_id_fkey", ondelete="CASCADE"
        ),
        nullable=False,
    )
    reference_id = Column(String, nullable=False)
    reference_type = Column(EnumColumn(CommentReferenceType), nullable=False)

    __table_args__ = (
        Index("ix_comment_reference_reference_id", "reference_id"),
        Index("ix_comment_reference_reference_type", "reference_type"),
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

    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user_id = Column(
        String, ForeignKey("fidesuser.id", ondelete="SET NULL"), nullable=True
    )
    parent_id = Column(
        String(255),
        ForeignKey("comment.id", name="comment_parent_id_fkey", ondelete="SET NULL"),
        nullable=True,
    )
    # Not all users in the system have a username, and users can be deleted.
    # Store a non-normalized copy of username for these cases.
    username = Column(String, nullable=True)
    comment_text = Column(String, nullable=False)
    comment_type = Column(EnumColumn(CommentType), nullable=False)

    __table_args__ = (Index("ix_comment_parent_id", "parent_id"),)

    parent = relationship(
        "Comment",
        remote_side="Comment.id",
        foreign_keys=[parent_id],
        back_populates="replies",
        uselist=False,
    )

    replies = relationship(
        "Comment",
        foreign_keys=[parent_id],
        back_populates="parent",
        uselist=True,
        order_by="Comment.created_at",
        passive_deletes=True,
    )

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

    attachments = relationship(
        "Attachment",
        secondary="attachment_reference",
        primaryjoin="and_(Comment.id == AttachmentReference.reference_id, "
        "AttachmentReference.reference_type == 'comment')",
        secondaryjoin="Attachment.id == AttachmentReference.attachment_id",
        order_by="Attachment.created_at",
        viewonly=True,
        uselist=True,
    )

    def delete(self, db: Session) -> None:
        """Delete the comment, its replies, and all associated references.

        Replies are deleted explicitly rather than via ON DELETE CASCADE to ensure
        each reply's attachments and references are cleaned up properly. The FK
        uses SET NULL as a safety net: if a comment is deleted outside this method,
        replies become orphans rather than being silently cascade-deleted without
        attachment cleanup.

        Uses iterative traversal to avoid unbounded recursion and session state
        hazards from lazy loading mid-delete.
        """
        # TODO (ENG-3299): When message_to_subject / reply_from_subject CommentTypes
        # are added, prevent deletion of comments with those types to preserve
        # correspondence threads.

        # Re-fetch from the DB to guarantee a session-bound instance.
        # Callers (e.g. test fixture teardown) may hold a detached reference,
        # which would raise DetachedInstanceError on any lazy relationship access.
        comment = db.query(Comment).filter(Comment.id == self.id).first()
        if comment is None:
            logger.debug("Comment {} already deleted, skipping", self.id)
            return

        # Collect all descendants iteratively (breadth-first)
        to_delete = []
        stack = list(comment.replies)
        while stack:
            node = stack.pop()
            stack.extend(node.replies)
            to_delete.append(node)

        # Delete children before parents (reverse of discovery order)
        for node in reversed(to_delete):
            AttachmentService(db).delete_for_reference(
                node.id, AttachmentReferenceType.comment
            )
            for reference in node.references:
                reference.delete(db)
            db.delete(node)

        # Delete self
        AttachmentService(db).delete_for_reference(
            comment.id, AttachmentReferenceType.comment
        )
        for reference in comment.references:
            reference.delete(db)
        db.delete(comment)

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
            # If a reply has its own CommentReference (e.g. ENG-3299
            # correspondence types), it may appear in the query AND be
            # reached via a parent's delete() BFS — skip already-deleted.
            if comment not in db.deleted:
                comment.delete(db)
