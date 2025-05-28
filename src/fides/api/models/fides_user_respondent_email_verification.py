from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from citext import CIText
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.cryptography.cryptographic_util import generate_secure_random_string
from fides.api.db.base_class import Base

ACCESS_LINK_TTL_DAYS = 7  # Access links stay active for 7 days
VERIFICATION_CODE_TTL_HOURS = 1  # Verification codes expire after 1 hour


class FidesUserRespondentEmailVerification(Base):
    """Model for handling email verification for external respondents.

    This handles two types of verification:
    1. Access links - long-lived (7 days) for initial access
    2. Verification codes - short-lived (1 hour) for actual verification
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "fides_user_respondent_email_verification"

    username = Column(  # type: ignore
        CIText,
        ForeignKey("fidesuser.username", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_token = Column(
        String, nullable=False, unique=True, index=True
    )  # Token for the access link
    access_token_expires_at = Column(DateTime(timezone=True), nullable=False)
    verification_code = Column(
        String, nullable=True
    )  # Optional until access link is used
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    attempts = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = False
    ) -> FidesUserRespondentEmailVerification:
        """
        Create a FidesUserEmailVerification record with a new access token.
        The verification code will be generated when the access link is used.
        """
        # Generate a secure token for the access link
        access_token = generate_secure_random_string(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=ACCESS_LINK_TTL_DAYS)

        verification = super().create(
            db,
            data={
                "id": generate_secure_random_string(16),  # Generate a unique ID
                "username": data["username"],
                "access_token": access_token,
                "access_token_expires_at": expires_at,
                "attempts": 0,
            },
        )

        return verification

    def is_access_token_expired(self) -> bool:
        """Check if the access token has expired."""
        if not self.access_token_expires_at:
            return True

        current_time_utc = datetime.now(timezone.utc)
        return current_time_utc > self.access_token_expires_at

    def is_verification_code_expired(self) -> bool:
        """Check if the verification code has expired."""
        if not self.verification_code_expires_at:
            return True

        current_time_utc = datetime.now(timezone.utc)
        return current_time_utc > self.verification_code_expires_at

    def verify_access_token(self, token: str) -> bool:
        """Verify the access token and generate a verification code if valid."""
        if self.is_access_token_expired():
            return False

        return self.access_token == token

    def generate_verification_code(self, db: Session) -> str:
        """Generate a new verification code when access link is used."""
        # Generate a 6-digit numeric code
        code = generate_secure_random_string(6, numeric_only=True)
        self.verification_code = code
        self.verification_code_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=VERIFICATION_CODE_TTL_HOURS
        )
        self.attempts = 0
        self.save(db)
        return code

    def verify_code(self, code: str, db: Session) -> bool:
        """Verify the provided code and track attempts."""
        if self.is_verification_code_expired():
            return False

        self.attempts += 1
        self.save(db)

        return self.verification_code == code

    def generate_new_access_token(self, db: Session) -> str:
        """Generate a new access token and reset attempts."""
        token = generate_secure_random_string(32)
        self.access_token = token
        self.access_token_expires_at = datetime.now(timezone.utc) + timedelta(
            days=ACCESS_LINK_TTL_DAYS
        )
        self.attempts = 0
        self.save(db)
        return token
