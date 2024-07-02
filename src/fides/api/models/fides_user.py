# pylint: disable=unused-import
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, List

from citext import CIText
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import String
from sqlalchemy.orm import Session, relationship

from fides.api.common_exceptions import SystemManagerException
from fides.api.cryptography.cryptographic_util import generate_salt, hash_with_salt
from fides.api.db.base_class import Base
from fides.api.models.audit_log import AuditLog

# Intentionally importing SystemManager here to build the FidesUser.systems relationship
from fides.api.models.system_manager import SystemManager  # type: ignore[unused-import]
from fides.api.schemas.user import DisabledReason

if TYPE_CHECKING:
    from fides.api.models.sql_models import System  # type: ignore[attr-defined]


class FidesUser(Base):
    """The DB ORM model for FidesUser."""

    username = Column(CIText, unique=True, index=True)
    email_address = Column(CIText, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    disabled = Column(Boolean, nullable=False, server_default="f")
    disabled_reason = Column(EnumColumn(DisabledReason), nullable=True)
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

    systems = relationship("System", secondary="systemmanager", back_populates="data_stewards")  # type: ignore

    @property
    def system_ids(self) -> List[str]:
        return [system.id for system in self.systems]

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
    def create(
        cls, db: Session, data: dict[str, Any], check_name: bool = True
    ) -> FidesUser:
        """Create a FidesUser by hashing the password with a generated salt
        and storing the hashed password and the salt"""

        # we set a dummy password if one isn't provided because this means it's part of the user
        # invite flow and the password will be set by the user after they accept their invite
        hashed_password, salt = FidesUser.hash_password(
            data.get("password") or str(uuid.uuid4())
        )

        user = super().create(
            db,
            data={
                "salt": salt,
                "hashed_password": hashed_password,
                "username": data["username"],
                "email_address": data.get("email_address"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "disabled": data.get("disabled") or False,
                "disabled_reason": data.get("disabled_reason"),
            },
            check_name=check_name,
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

    def set_as_system_manager(self, db: Session, system: System) -> None:
        """Add a user as one of the system managers for the given system
        If applicable, also update the systems on the user's client
        """
        if (
            not type(system).__name__ == "System"
        ):  # Checking type instead of with isinstance to avoid import errors
            raise SystemManagerException(
                "Must pass in a system to set user as system manager."
            )

        if self in system.data_stewards:
            raise SystemManagerException(
                f"User '{self.username}' is already a system manager of '{system.name}'."
            )

        self.systems.append(system)
        self.save(db=db)

        if self.client:
            self.client.update(db=db, data={"systems": self.system_ids})

    def remove_as_system_manager(self, db: Session, system: System) -> None:
        """Remove a user as one of the system managers for the given system
        If applicable, also update the systems on the user's client
        """
        if not type(system).__name__ == "System":
            raise SystemManagerException(
                "Must pass in a system to remove user as system manager."
            )

        try:
            self.systems.remove(system)
            self.save(db=db)
        except ValueError:
            raise SystemManagerException(
                f"User '{self.username}' is not a manager of system '{system.name}'."
            )

        if self.client:
            self.client.update(db=db, data={"systems": self.system_ids})
