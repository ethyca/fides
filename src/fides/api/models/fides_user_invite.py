from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from citext import CIText
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.cryptography.cryptographic_util import (
    generate_salt,
    hash_credential_with_salt,
)
from fides.api.db.base_class import Base

INVITE_CODE_TTL_HOURS = 24


class FidesUserInvite(Base):
    @declared_attr
    def __tablename__(self) -> str:
        return "fides_user_invite"

    username = Column(  # type: ignore
        CIText,
        ForeignKey("fidesuser.username", ondelete="CASCADE"),
        primary_key=True,
    )
    hashed_invite_code = Column(String, nullable=False)
    salt = Column(String, nullable=False)

    @classmethod
    def hash_invite_code(
        cls, invite_code: str, encoding: str = "UTF-8"
    ) -> tuple[str, str]:
        """Utility function to hash a user's invite code with a generated salt."""

        salt = generate_salt()
        hashed_invite_code = hash_credential_with_salt(
            invite_code.encode(encoding),
            salt.encode(encoding),
        )
        return hashed_invite_code, salt

    @classmethod
    def create(
        cls, db: Session, *, data: dict[str, Any], check_name: bool = False
    ) -> FidesUserInvite:
        """
        Create a FidesUserInvite by hashing the invite code with a generated salt
        and storing the hashed invite code and the salt.
        """

        hashed_invite_code, salt = FidesUserInvite.hash_invite_code(data["invite_code"])

        user_invite = super().create(
            db,
            data={
                "username": data["username"],
                "hashed_invite_code": hashed_invite_code,
                "salt": salt,
            },
        )

        return user_invite

    def invite_code_valid(self, invite_code: str, encoding: str = "UTF-8") -> bool:
        """Verifies that the provided invite code is correct."""
        if self.salt is None:
            return False

        invite_code_hash = hash_credential_with_salt(
            invite_code.encode(encoding),
            self.salt.encode(encoding),
        )

        return invite_code_hash == self.hashed_invite_code

    def is_expired(self) -> bool:
        """Check if the invite has expired."""

        current_time_utc = datetime.now(timezone.utc)

        if not self.updated_at:
            return True

        expiration_datetime = self.updated_at + timedelta(hours=INVITE_CODE_TTL_HOURS)
        return current_time_utc > expiration_datetime

    def renew_invite(self, db: Session, new_invite_code: str) -> None:
        """Updates the invite code and extends the expiration."""

        hashed_invite_code, salt = FidesUserInvite.hash_invite_code(new_invite_code)
        self.hashed_invite_code = hashed_invite_code
        self.salt = salt
        self.save(db)
