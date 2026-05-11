"""Identity verification codes for PrivacyRequest / ConsentRequest / email verification."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from fides.api.db.base_class import Base


class IdentityVerificationCode(Base):
    """Hashed verification code and attempt metadata per logical owner."""

    __tablename__ = "identity_verification_code"
    __table_args__ = (
        UniqueConstraint(
            "owner_type",
            "owner_id",
            name="uq_identity_verification_code_owner",
        ),
    )

    owner_id = Column(String, nullable=False, index=True)
    owner_type = Column(String, nullable=False, index=True)
    code_hash = Column(String, nullable=False)
    attempt_count = Column(Integer, nullable=False, server_default="0")
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
