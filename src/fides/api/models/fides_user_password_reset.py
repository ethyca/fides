from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.cryptography.cryptographic_util import (
    generate_salt,
    hash_credential_with_salt,
)
from fides.api.db.base_class import Base
from fides.config import CONFIG

DEFAULT_PASSWORD_RESET_TOKEN_TTL_MINUTES = 30


class FidesUserPasswordReset(Base):
    """Stores hashed password reset tokens for self-service forgot-password flow."""

    @declared_attr
    def __tablename__(self) -> str:
        return "fides_user_password_reset"

    user_id = Column(
        String,
        ForeignKey("fidesuser.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_token = Column(String, nullable=False)
    salt = Column(String, nullable=False)

    @classmethod
    def hash_token(cls, token: str, encoding: str = "UTF-8") -> tuple[str, str]:
        """Hash a reset token with a generated salt."""
        salt = generate_salt()
        hashed_token = hash_credential_with_salt(
            token.encode(encoding),
            salt.encode(encoding),
        )
        return hashed_token, salt

    @classmethod
    def create_or_replace(
        cls, db: Session, *, user_id: str, token: str
    ) -> FidesUserPasswordReset:
        """Create a password reset record, replacing any existing one for this user."""
        existing = cls.get_by(db, field="user_id", value=user_id)
        if existing:
            existing.delete(db)

        hashed_token, salt = cls.hash_token(token)
        return super().create(
            db,
            data={
                "user_id": user_id,
                "hashed_token": hashed_token,
                "salt": salt,
            },
        )

    def token_valid(self, token: str, encoding: str = "UTF-8") -> bool:
        """Verify that the provided token matches the stored hash."""
        if self.salt is None:
            return False

        token_hash = hash_credential_with_salt(
            token.encode(encoding),
            self.salt.encode(encoding),
        )
        return token_hash == self.hashed_token

    def is_expired(self) -> bool:
        """Check if the reset token has expired."""
        current_time_utc = datetime.now(timezone.utc)

        if not self.created_at:
            return True

        ttl_minutes = getattr(
            CONFIG.security,
            "password_reset_token_ttl_minutes",
            DEFAULT_PASSWORD_RESET_TOKEN_TTL_MINUTES,
        )
        expiration_datetime = self.created_at + timedelta(minutes=ttl_minutes)
        return current_time_utc > expiration_datetime
