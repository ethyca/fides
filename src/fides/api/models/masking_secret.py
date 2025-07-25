from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union
from urllib.parse import unquote_to_bytes

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base, JSONTypeOverride
from fides.api.util.custom_json_encoder import ENCODED_BYTES_PREFIX
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.privacy_request import PrivacyRequest


class MaskingSecret(Base):
    """SQLAlchemy model for storing secret caching information"""

    @declared_attr
    def __tablename__(self) -> str:
        return "masking_secret"

    privacy_request_id = Column(
        String, ForeignKey("privacyrequest.id", ondelete="CASCADE"), nullable=False
    )
    secret = Column(
        StringEncryptedType(
            JSONTypeOverride,
            CONFIG.security.app_encryption_key,
            AesGcmEngine,
            "pkcs5",
        ),
        nullable=False,
    )
    masking_strategy = Column(String, nullable=False)
    secret_type = Column(String, nullable=False)
    privacy_request = relationship("PrivacyRequest", back_populates="masking_secrets")

    def set_secret(self, secret: Union[str, bytes]) -> None:
        """Set the secret value, handling both string and bytes types"""
        if isinstance(secret, str):
            self.secret = secret.encode("utf-8")
        elif isinstance(secret, bytes):
            self.secret = secret
        else:
            raise ValueError("Secret must be either string or bytes")

    def get_secret(self) -> Union[str, bytes]:
        """Retrieve the secret in its original type"""
        secret = self.secret
        if isinstance(secret, str) and secret.startswith(ENCODED_BYTES_PREFIX):
            return unquote_to_bytes(secret)[len(ENCODED_BYTES_PREFIX) :]
        return secret

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> "MaskingSecret":
        """
        Create a new masking secret. Handles both string and bytes secrets automatically, encrypting them for storage.
        """
        return super().create(db=db, data=data, check_name=check_name)
