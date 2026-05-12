"""Manual webhook connector input persisted for a privacy request."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.db.encryption_utils import encrypted_type


class ManualWebhookInput(Base):
    """Stores validated manual webhook payload per (privacy request, webhook, action)."""

    __tablename__ = "lethe_manual_webhook_input"
    __table_args__ = (
        UniqueConstraint(
            "privacy_request_id",
            "manual_webhook_id",
            "action_type",
            name="uq_lethe_manual_webhook_input_pr_webhook_action",
        ),
    )

    privacy_request_id = Column(
        String,
        ForeignKey("privacyrequest.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    manual_webhook_id = Column(
        String,
        ForeignKey("accessmanualwebhook.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type = Column(String, nullable=False)
    input_data = Column(encrypted_type(type_in=JSONTypeOverride), nullable=False)
