"""SQLAlchemy model for chat provider configuration (Slack, Teams, etc.)."""

from typing import Any, Dict, Optional

from sqlalchemy import Boolean, CheckConstraint, Column, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base
from fides.config import CONFIG


class ChatProviderConfig(Base):
    """
    Stores configuration for chat providers (Slack, Microsoft Teams, etc.).

    This is a single-row table. The single record describes the organization's
    chat provider configuration for notifications and alerts.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "chat_provider_config"

    provider_type = Column(String, nullable=False, default="slack")
    workspace_url = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    client_secret = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=True,
    )
    access_token = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=True,
    )
    enabled = Column(Boolean, nullable=False, default=False)
    single_row = Column(Boolean, nullable=False, default=True)
    workspace_name = Column(String, nullable=True)
    connected_by_email = Column(String, nullable=True)
    notification_channel_id = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("single_row", name="chat_provider_config_single_row_check"),
    )

    @classmethod
    def get_config(cls, db: Session) -> Optional["ChatProviderConfig"]:
        """
        Get the chat provider config record.
        Returns None if no config exists.
        """
        return db.query(cls).first()

    @classmethod
    def get_or_create(cls, db: Session) -> "ChatProviderConfig":
        """
        Get the existing chat provider config or create a new one with defaults.
        """
        existing = cls.get_config(db)
        if existing:
            return existing

        return cls.create(
            db=db,
            data={
                "provider_type": "slack",
                "enabled": False,
            },
        )

    @classmethod
    def update_config(
        cls, db: Session, data: Dict[str, Any]
    ) -> "ChatProviderConfig":
        """
        Update the chat provider config, creating it if it doesn't exist.
        """
        config = cls.get_or_create(db)
        config.update(db=db, data=data)
        return config

    @property
    def authorized(self) -> bool:
        """Check if the provider has been authorized (has an access token)."""
        return self.access_token is not None
