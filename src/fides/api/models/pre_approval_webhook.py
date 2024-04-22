from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import Session, relationship  # type: ignore

from fides.api.db.base_class import Base


class PreApprovalWebhook(Base):
    name = Column(String, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    connection_config_id = Column(
        String, ForeignKey("connectionconfig.id"), nullable=False
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
    webhook_id = Column(
        String, ForeignKey(PreApprovalWebhook.id_field_path), nullable=False
    )
    privacy_request_id = Column(
        String, ForeignKey("privacyrequest.id", ondelete="SET NULL"), index=True
    )  # Which privacy request this webhook response belongs to
    is_eligible = Column(Boolean, nullable=False)
    privacy_request = relationship(
        "PrivacyRequest", back_populates="pre_approval_webhook_replies", uselist=False  # type: ignore
    )
