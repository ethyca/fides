from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

from fides.api.cryptography.cryptographic_util import generate_secure_random_string
from fides.api.db.base_class import Base
from fides.api.util.identity_verification import IdentityVerificationMixin
from fides.config import get_config

CONFIG = get_config()


if TYPE_CHECKING:
    from fides.api.models.fides_user import FidesUser

# Access links stay active for 45 days - the same as the DSR expiration. A new link is generated for each email.
# The emails are created for new DSRs which are assigned to the respondent.
ACCESS_LINK_TTL_DAYS = 45


class FidesUserRespondentEmailVerification(Base, IdentityVerificationMixin):
    """Model for handling email verification for external respondents.

    This handles two types of verification:
    1. Access links - long-lived (45 days) for initial access
    2. Verification codes - short-lived (1 hour) for actual verification

    When an email is sent to an external respondent, a new verification is created with a new access token is created.
    When a respondent clicks the link in the email, the access token is verified and a verification code is generated.
    The verification code is sent to the respondent's email address and the respondent is prompted to enter the code.
    Verification is handled by the `IdentityVerificationMixin` class.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "fides_user_respondent_email_verification"

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
    identity_verified_at = Column(DateTime(timezone=True), nullable=True)

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
                "user_id": data["user_id"],
                "access_token": access_token,
                "access_token_expires_at": expires_at,
            },
        )

        return verification

    def is_access_token_expired(self) -> bool:
        """Check if the access token has expired."""
        if not self.access_token_expires_at:
            return True

        current_time_utc = datetime.now(timezone.utc)
        return current_time_utc > self.access_token_expires_at

    def verify_access_token(self, token: str) -> bool:
        """Verify the access token and generate a verification code if valid."""
        if self.is_access_token_expired():
            return False

        return self.access_token == token

    def verify_identity(
        self,
        db: Session,
        provided_code: Optional[str] = None,
    ) -> None:
        """A method to call the internal identity verification method provided by the
        `IdentityVerificationMixin`."""
        if self.is_access_token_expired():
            raise ValueError("Access token has expired.")

        self._verify_identity(provided_code=provided_code)
        self.identity_verified_at = datetime.now(timezone.utc)
        self.save(db)
