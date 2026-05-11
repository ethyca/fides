"""Identity verification storage backed by Postgres (replaces Redis keys)."""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, cast
from uuid import uuid4

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.common_exceptions import IdentityVerificationException
from fides.config import CONFIG

from lethe.state.models.identity_verification_code import IdentityVerificationCode


def _owner_type(obj: object) -> str:
    return obj.__class__.__name__


def _code_hmac(owner_type: str, owner_id: str, code: str) -> str:
    return hmac.new(
        f"{owner_type}:{owner_id}:lethe-identity-v1".encode("utf-8"),
        code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class IdentityVerificationMixin:
    """Common identity verification logic for SQLAlchemy models with an ``id``."""

    def _identity_db(self) -> Session:
        db = Session.object_session(self)
        if db is None:
            raise RuntimeError(f"{self.__class__.__name__} is not bound to a session")
        return db

    def cache_identity_verification_code(self, value: str) -> None:
        db = self._identity_db()
        owner_id = cast(str, self.id)
        owner_type = _owner_type(self)
        expires_at = datetime.utcnow() + timedelta(
            seconds=int(CONFIG.redis.identity_verification_code_ttl_seconds)
        )
        digest = _code_hmac(owner_type, owner_id, value)
        existing = (
            db.query(IdentityVerificationCode)
            .filter(
                IdentityVerificationCode.owner_id == owner_id,
                IdentityVerificationCode.owner_type == owner_type,
            )
            .first()
        )
        if existing:
            existing.code_hash = digest
            existing.attempt_count = 0
            existing.expires_at = expires_at
        else:
            db.add(
                IdentityVerificationCode(
                    id=f"ivc_{uuid4()}",
                    owner_id=owner_id,
                    owner_type=owner_type,
                    code_hash=digest,
                    attempt_count=0,
                    expires_at=expires_at,
                )
            )
        db.flush()

    def _increment_verification_code_attempt_count(self) -> None:
        db = self._identity_db()
        owner_id = cast(str, self.id)
        owner_type = _owner_type(self)
        row = (
            db.query(IdentityVerificationCode)
            .filter(
                IdentityVerificationCode.owner_id == owner_id,
                IdentityVerificationCode.owner_type == owner_type,
            )
            .first()
        )
        if not row:
            return
        row.attempt_count = int(row.attempt_count or 0) + 1
        db.flush()

    def get_cached_verification_code(self) -> Optional[str]:
        """Not supported for hashed storage; returns ``None``."""
        return None

    def _get_cached_verification_code_attempt_count(self) -> int:
        db = self._identity_db()
        owner_id = cast(str, self.id)
        owner_type = _owner_type(self)
        row = (
            db.query(IdentityVerificationCode)
            .filter(
                IdentityVerificationCode.owner_id == owner_id,
                IdentityVerificationCode.owner_type == owner_type,
            )
            .first()
        )
        if not row:
            return 0
        return int(row.attempt_count or 0)

    def purge_verification_code(self) -> None:
        db = self._identity_db()
        owner_id = cast(str, self.id)
        owner_type = _owner_type(self)
        logger.debug(
            "Removing identity verification row for record with ID: {}",
            owner_id,
        )
        db.query(IdentityVerificationCode).filter(
            IdentityVerificationCode.owner_id == owner_id,
            IdentityVerificationCode.owner_type == owner_type,
        ).delete(synchronize_session=False)
        db.flush()

    def _verify_identity(self, provided_code: Optional[str] = None) -> None:
        if not provided_code:
            raise IdentityVerificationException(
                f"Identification code missing for {self.id}."  # type: ignore[attr-defined]
            )

        db = self._identity_db()
        owner_id = cast(str, self.id)
        owner_type = _owner_type(self)
        row = (
            db.query(IdentityVerificationCode)
            .filter(
                IdentityVerificationCode.owner_id == owner_id,
                IdentityVerificationCode.owner_type == owner_type,
            )
            .first()
        )
        if not row or row.expires_at < datetime.utcnow():
            raise IdentityVerificationException(
                f"Identification code expired for {self.id}."  # type: ignore[attr-defined]
            )

        attempt_count = int(row.attempt_count or 0)
        if attempt_count >= CONFIG.security.identity_verification_attempt_limit:
            logger.debug(
                "Failed identity verification attempt limit exceeded for record with ID: {}",
                owner_id,
            )
            self.purge_verification_code()
            raise PermissionError(f"Attempt limit hit for '{self.id}'")  # type: ignore[attr-defined]

        expected = row.code_hash
        actual = _code_hmac(owner_type, owner_id, provided_code)
        if not hmac.compare_digest(expected, actual):
            self._increment_verification_code_attempt_count()
            raise PermissionError(f"Incorrect identification code for '{self.id}'")  # type: ignore[attr-defined]
