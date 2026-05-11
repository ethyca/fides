"""Manual webhook input persisted for DSR pipeline (replaces Redis EN_WEBHOOK_* keys)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.db.encryption_utils import encrypted_type

if TYPE_CHECKING:
    pass


class ManualWebhookInput(Base):
    """Stores manual webhook connector input per privacy request, webhook, and action type."""

    __tablename__ = "manual_webhook_input"
    __table_args__ = (
        UniqueConstraint(
            "privacy_request_id",
            "manual_webhook_id",
            "action_type",
            name="uq_manual_webhook_input_pr_webhook_action",
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

    privacy_request = relationship(
        "PrivacyRequest",
        back_populates="manual_webhook_inputs",
    )
    manual_webhook = relationship(
        "AccessManualWebhook",
        back_populates="manual_webhook_inputs",
    )

    @classmethod
    def get_for(
        cls,
        db: Session,
        *,
        privacy_request_id: str,
        manual_webhook_id: str,
        action_type: str,
    ) -> Optional["ManualWebhookInput"]:
        return (
            db.query(cls)
            .filter_by(
                privacy_request_id=privacy_request_id,
                manual_webhook_id=manual_webhook_id,
                action_type=action_type,
            )
            .first()
        )
