from sqlalchemy import Column
from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import Session, backref, declared_attr, relationship  # type: ignore
from fides.api.db.base_class import Base
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.privacy_request import (
    PrivacyRequest,
)


class PreApprovalWebhook(Base):
    name = Column(String, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    connection_config_id = Column(
        String, ForeignKey(ConnectionConfig.id_field_path), nullable=False
    )
    connection_config = relationship(
        ConnectionConfig, back_populates="pre_approval_webhook", uselist=False
    )


class PreApprovalWebhookReply(Base):
    webhook_id = Column(
        String, ForeignKey(PreApprovalWebhook.id_field_path), nullable=False
    )
    privacy_request_id = Column(
        String, ForeignKey(PrivacyRequest.id, ondelete="SET NULL"), index=True
    )  # Which privacy request this webhook response belongs to
    is_eligible = Column(Boolean, nullable=False)
    privacy_request = relationship(PrivacyRequest, back_populates="pre_approval_webhook_response")
