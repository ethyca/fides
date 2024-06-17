from sqlalchemy import Boolean, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Session, relationship  # type: ignore

from fides.api.db.base_class import Base


class PreApprovalWebhook(Base):
    """
    An HTTPS callback that calls an external REST API endpoint as soon as a privacy request
    is received (or after user identity verification, if applicable).
    """

    name = Column(String, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    connection_config_id = (
        Column(  # Deleting a Connection Config also deletes the Pre Approval Webhook
            String,
            ForeignKey("connectionconfig.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    connection_config = relationship(
        "ConnectionConfig", back_populates="pre_approval_webhooks", uselist=False  # type: ignore
    )

    @classmethod
    def persist_obj(
        cls, db: Session, resource: "PreApprovalWebhook"
    ) -> "PreApprovalWebhook":
        """Override to have PreApprovalWebhooks not be committed to the database automatically."""
        db.add(resource)
        return resource


class PreApprovalWebhookReply(Base):
    """
    Stores the callback response to the PreApprovalWebhook to determine if the Privacy
    Request is eligible to be automatically approved
    """

    webhook_id = Column(
        String,
        ForeignKey(PreApprovalWebhook.id_field_path, ondelete="SET NULL"),
        index=True,
    )
    privacy_request_id = Column(
        String, ForeignKey("privacyrequest.id", ondelete="SET NULL"), index=True
    )  # Which privacy request this webhook response belongs to
    is_eligible = Column(Boolean, nullable=False)

    privacy_request = relationship(
        "PrivacyRequest", back_populates="pre_approval_webhook_replies", uselist=False  # type: ignore
    )

    __table_args__ = (
        UniqueConstraint(
            "webhook_id", "privacy_request_id", name="webhook_id_privacy_request_id"
        ),
    )
