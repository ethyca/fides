"""SQLAlchemy model for chat provider configuration (Slack, Teams, etc.)."""

from sqlalchemy import Boolean, Column, String, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base
from fides.config import CONFIG


class ChatProviderConfig(Base):
    """
    Stores configuration for chat providers (Slack, Microsoft Teams, etc.).

    Multiple configurations can exist (e.g., different Slack workspaces),
    but only one can be enabled at a time globally.

    Note: All query operations are handled by ChatProviderService in fidesplus.
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
    signing_secret = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=True,
    )
    enabled = Column(Boolean, nullable=False, default=False)
    workspace_name = Column(String, nullable=True)
    connected_by_email = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "workspace_url", name="chat_provider_config_workspace_url_unique"
        ),
    )

    @property
    def authorized(self) -> bool:
        """Check if the provider has been authorized (has an access token)."""
        return self.access_token is not None
