from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import Session, relationship

from fides.lib.cryptography.cryptographic_util import generate_salt, hash_with_salt
from fides.lib.db.base_class import Base
from fides.lib.models.audit_log import AuditLog


class FidesUser(Base):
    """The DB ORM model for FidesUser."""

    username = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_at = Column(DateTime(timezone=True), nullable=True)

    # passive_deletes="all" prevents audit logs from having their
    # privacy_request_id set to null when a privacy_request is deleted.
    # We want to retain for record-keeping.
    audit_logs = relationship(
        AuditLog,
        backref="fides_user",
        lazy="dynamic",
        passive_deletes="all",
        primaryjoin="foreign(AuditLog.user_id)==FidesUser.id",
    )

    client = relationship(  # type: ignore
        "ClientDetail", backref="user", cascade="all, delete", uselist=False
    )

    @classmethod
    def hash_password(cls, password: str, encoding: str = "UTF-8") -> tuple[str, str]:
        """Utility function to hash a user's password with a generated salt"""
        salt = generate_salt()
        hashed_password = hash_with_salt(
            password.encode(encoding),
            salt.encode(encoding),
        )
        return hashed_password, salt

    @classmethod
    def create(cls, db: Session, data: dict[str, Any]) -> FidesUser:
        """Create a FidesUser by hashing the password with a generated salt
        and storing the hashed password and the salt"""
        hashed_password, salt = FidesUser.hash_password(data["password"])

        user = super().create(
            db,
            data={
                "salt": salt,
                "hashed_password": hashed_password,
                "username": data["username"],
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
            },
        )

        return user  # type: ignore

    def credentials_valid(self, password: str, encoding: str = "UTF-8") -> bool:
        """Verifies that the provided password is correct."""
        provided_password_hash = hash_with_salt(
            password.encode(encoding),
            self.salt.encode(encoding),
        )

        return provided_password_hash == self.hashed_password

    def update_password(self, db: Session, new_password: str) -> None:
        """Updates the user's password to the specified value.

        No validations are performed on the old/existing password within this function.
        """

        hashed_password, salt = FidesUser.hash_password(new_password)
        self.hashed_password = hashed_password  # type: ignore
        self.salt = salt  # type: ignore
        self.password_reset_at = datetime.utcnow()  # type: ignore
        self.save(db)
