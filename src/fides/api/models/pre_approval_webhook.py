from sqlalchemy import Column
from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import relationship  # type: ignore
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


class PreApprovalWebhookReply(Base):
    webhook_id = Column(
        String, ForeignKey(PreApprovalWebhook.id_field_path), nullable=False
    )
    privacy_request_id = Column(
        String, ForeignKey("privacyrequest.id", ondelete="SET NULL"), index=True
    )  # Which privacy request this webhook response belongs to
    is_eligible = Column(Boolean, nullable=False)
    privacy_request = relationship(
        "PrivacyRequest", back_populates="pre_approval_webhook_reply"  # type: ignore
    )
