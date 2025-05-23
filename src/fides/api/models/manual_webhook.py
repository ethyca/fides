from typing import Any, Optional

from loguru import logger
from pydantic import ConfigDict, create_model
from sqlalchemy import Column, ForeignKey, String, or_, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base
from fides.api.models.attachment import Attachment, AttachmentReference
from fides.api.models.comment import Comment, CommentReference
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.policy import ActionType


class AccessManualWebhook(Base):
    """Describes a manual datasource that will be used for access requests.

    These data sources are not treated as part of the traversal.  Data uploaded
    for an AccessManualWebhook is passed on as-is to the end user and is
    not consumed as part of the graph.
    """

    connection_config_id = Column(
        String,
        ForeignKey(ConnectionConfig.id_field_path),
        unique=True,
        nullable=False,
    )
    connection_config = relationship(
        ConnectionConfig, back_populates="access_manual_webhook", uselist=False
    )

    attachments = relationship(
        "Attachment",
        secondary="attachment_reference",
        primaryjoin="and_(AccessManualWebhook.id == AttachmentReference.reference_id, "
        "AttachmentReference.reference_type == 'access_manual_webhook')",
        secondaryjoin="Attachment.id == AttachmentReference.attachment_id",
        order_by="Attachment.created_at",
        viewonly=True,
        uselist=True,
    )

    comments = relationship(
        "Comment",
        secondary="comment_reference",
        primaryjoin="and_(AccessManualWebhook.id == CommentReference.reference_id, "
        "CommentReference.reference_type == 'access_manual_webhook')",
        secondaryjoin="Comment.id == CommentReference.comment_id",
        order_by="Comment.created_at",
        viewonly=True,
        uselist=True,
    )

    fields = Column(MutableList.as_mutable(JSONB), nullable=False)

    def access_field_definitions(self) -> dict[str, Any]:
        """Shared access field definitions for manual webhook schemas"""
        field_definitions = {}
        for field in self.fields or []:
            # Include all fields for access, regardless of type
            if "dsr_package_label" in field:
                field_definitions[field["dsr_package_label"]] = (Optional[str], None)
        return field_definitions

    def erasure_field_definitions(self) -> dict[str, Any]:
        """Shared erasure field definitions for manual webhook schemas"""
        field_definitions = {}
        for field in self.fields or []:
            # Use types if present, otherwise default to ["string"]
            field_types = field.get("types", ["string"])
            # Only include string fields for erasure
            if "dsr_package_label" in field and "string" in field_types:
                field_definitions[field["dsr_package_label"]] = (Optional[bool], None)
        return field_definitions

    @property
    def fields_schema(self) -> FidesSchema:
        """Build a dynamic Pydantic schema from fields defined on this webhook"""

        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            __config__=ConfigDict(extra="forbid"),
            **self.access_field_definitions(),
        )

    @property
    def erasure_fields_schema(self) -> FidesSchema:
        """
        Build a dynamic Pydantic schema from fields defined on this webhook.
        The fields in the schema for erasure input validation are of type bool,
        vs str for access input validation.
        """
        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            model_config=ConfigDict(extra="forbid"),
            **self.erasure_field_definitions(),
        )

    @property
    def fields_non_strict_schema(self) -> FidesSchema:
        """Returns a dynamic Pydantic Schema for webhook fields that can keep the overlap between
        fields that are saved and fields that are defined here."""
        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            __config__=ConfigDict(extra="ignore"),
            **self.access_field_definitions(),
        )

    @property
    def erasure_fields_non_strict_schema(self) -> FidesSchema:
        """Returns a dynamic Pydantic Schema for webhook fields that can keep the overlap between
        fields that are saved and fields that are defined here."""
        return create_model(  # type: ignore
            __model_name="ManualWebhookValidationModel",
            model_config=ConfigDict(extra="ignore"),
            **self.erasure_field_definitions(),
        )

    @property
    def empty_fields_dict(self) -> dict[str, None]:
        """Return a dictionary that maps defined dsr_package_labels to None

        Returned as a default if no data has been uploaded for a privacy request.
        """
        return {
            key: None
            for key in (self.fields_schema.schema().get("properties") or {}).keys()
        }

    @classmethod
    def get_enabled(
        cls, db: Session, action_type: Optional[ActionType] = None
    ) -> list["AccessManualWebhook"]:
        """Get all enabled access manual webhooks with fields"""

        query = db.query(cls).filter(
            AccessManualWebhook.connection_config_id == ConnectionConfig.id,
            ConnectionConfig.disabled.is_(False),
            AccessManualWebhook.fields != text("'null'"),
            AccessManualWebhook.fields != "[]",
        )

        # Add action_type filter only if action_type is provided
        if action_type is not None:
            query = query.filter(
                or_(
                    ConnectionConfig.enabled_actions.contains([action_type]),
                    ConnectionConfig.enabled_actions.is_(None),
                )
            )

        return query.all()

    def get_comment_by_id(self, db: Session, comment_id: str) -> Optional[Comment]:
        """Get the comment associated with the manual webhook"""
        comment = (
            db.query(Comment)
            .join(CommentReference, Comment.id == CommentReference.comment_id)
            .filter(
                CommentReference.reference_id == self.id,
                Comment.id == comment_id,
            )
            .first()
        )
        if not comment:
            logger.info(
                f"Comment with id {comment_id} not found on manual webhook {self.id}"
            )
        return comment

    def get_attachment_by_id(
        self, db: Session, attachment_id: str
    ) -> Optional[Attachment]:
        """Get the attachment associated with the manual webhook"""
        attachment = (
            db.query(Attachment)
            .join(
                AttachmentReference, Attachment.id == AttachmentReference.attachment_id
            )
            .filter(
                AttachmentReference.reference_id == self.id,
                Attachment.id == attachment_id,
            )
            .first()
        )
        if not attachment:
            logger.info(
                f"Attachment with id {attachment_id} not found on manual webhook {self.id}"
            )
        return attachment

    def delete_attachment_by_id(self, db: Session, attachment_id: str) -> None:
        """Delete the attachment associated with the manual webhook"""
        attachment = self.get_attachment_by_id(db, attachment_id)
        if attachment:
            attachment.delete(db)
