from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from fides.api.cryptography.cryptographic_util import generate_secure_random_string
from fides.api.db.base_class import Base, FidesBase
from fides.api.util.identity_verification import IdentityVerificationMixin
from fides.config import get_config

CONFIG = get_config()


if TYPE_CHECKING:
    from fides.api.models.fides_user import FidesUser

# Access links stay active for 30 days for external login functionality. A new link is generated for each email.
# The emails are created for new DSRs which are assigned to the respondent.
ACCESS_LINK_TTL_DAYS = 30


class FidesUserRespondentEmailVerification(Base, IdentityVerificationMixin):
    """Model for handling email verification for external respondents.

    This handles two types of verification:
    1. Access links - long-lived (30 days) for initial access
    2. Verification codes - short-lived (1 hour) for actual verification

    When an email is sent to an external respondent, a new verification is created with a new access token is created.
    When a respondent clicks the link in the email, the access token is verified and a verification code is generated.
    The verification code is sent to the respondent's email address and the respondent is prompted to enter the code.
    Verification is handled by the `IdentityVerificationMixin` class.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "fides_user_respondent_email_verification"

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
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
    identity_verified_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship(
        "FidesUser",
        back_populates="email_verifications",
        foreign_keys=[user_id],
    )

    __table_args__ = (
        Index(
            "ix_fides_user_respondent_email_verification_id",
            "id",
            unique=True,
        ),
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
