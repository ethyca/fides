from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from citext import CIText
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.cryptography.cryptographic_util import generate_secure_random_string
from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.fides_user import FidesUser

# Access links stay active for 45 days - the same as the DSR expiration. A new link is generated for each email.
# The emails are created for new DSRs which are assigned to the respondent.
ACCESS_LINK_TTL_DAYS = 45
VERIFICATION_CODE_TTL_HOURS = 1  # Verification codes expire after 1 hour


class FidesUserRespondentEmailVerification(Base):
    """Model for handling email verification for external respondents.

    This handles two types of verification:
    1. Access links - long-lived (7 days) for initial access
    2. Verification codes - short-lived (1 hour) for actual verification

    When an email is sent to an external respondent, a new verification is created with a new access token is created.
    When a respondent clicks the link in the email, the access token is verified and a verification code is generated.
    The verification code is sent to the respondent's email address and the respondent is prompted to enter the code.
    If the code is correct and has not expired, the respondent is considered verified.
    If the code is incorrect, the number of attempts is incremented and the verification is saved.
    If the user attempts to use a link with an expired access token the user is not verified.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "fides_user_respondent_email_verification"

    username = Column(  # type: ignore
        CIText,
        ForeignKey("fidesuser.username", ondelete="CASCADE"),
        nullable=True,
        index=False,
    )
    user_id = Column(
        String,
        ForeignKey("fidesuser.id", ondelete="CASCADE"),
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

    user = relationship(
        "FidesUser",
        back_populates="email_verifications",
        foreign_keys=[user_id],
    )

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
                "username": data["username"],
                "user_id": data["user_id"],
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
        # Generate a 16 character string
        # This is a hex string, so it will double the input parameter length
        code = generate_secure_random_string(8)
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
