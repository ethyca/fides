"""Identity verification codes stored in Postgres (replaces Redis identity verification keys)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base
from fides.config import CONFIG


def hash_verification_code(plaintext: str) -> str:
    """Deterministic hash for comparing verification codes at rest."""
    pepper = CONFIG.security.app_encryption_key or ""
    return hashlib.sha256(f"{pepper}:{plaintext}".encode("utf-8")).hexdigest()


class IdentityVerificationCode(Base):
    """One row per logical owner (privacy request, consent request, respondent verification)."""

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
    expires_at = Column(DateTime(timezone=True), nullable=False)

    @classmethod
    def get_for_owner(
        cls, db: Session, *, owner_id: str, owner_type: str
    ) -> Optional["IdentityVerificationCode"]:
        return db.query(cls).filter_by(owner_id=owner_id, owner_type=owner_type).first()

    @classmethod
    def upsert_code(
        cls,
        db: Session,
        *,
        owner_id: str,
        owner_type: str,
        plaintext_code: str,
        ttl_seconds: int,
    ) -> "IdentityVerificationCode":
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        existing = cls.get_for_owner(db, owner_id=owner_id, owner_type=owner_type)
        if existing:
            existing.code_hash = hash_verification_code(plaintext_code)
            existing.attempt_count = 0
            existing.expires_at = expires_at
            existing.save(db)
            return existing
        return cls.create(
            db=db,
            data={
                "owner_id": owner_id,
                "owner_type": owner_type,
                "code_hash": hash_verification_code(plaintext_code),
                "attempt_count": 0,
                "expires_at": expires_at,
            },
        )

    def matches(self, plaintext: str) -> bool:
        return hash_verification_code(plaintext) == self.code_hash
