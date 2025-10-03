# pylint: disable=unused-import
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, List

from citext import CIText
from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as EnumColumn
from sqlalchemy import String
from sqlalchemy.orm import Session, relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.common_exceptions import SystemManagerException
from fides.api.cryptography.cryptographic_util import (
    generate_salt,
    hash_credential_with_salt,
)
from fides.api.db.base_class import Base
from fides.api.models.audit_log import AuditLog

# Intentionally importing SystemManager here to build the FidesUser.systems relationship
from fides.api.schemas.user import DisabledReason
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.fides_user_permissions import FidesUserPermissions
    from fides.api.models.fides_user_respondent_email_verification import (
        FidesUserRespondentEmailVerification,
    )
    from fides.api.models.manual_task.manual_task import ManualTaskReference
    from fides.api.models.sql_models import System  # type: ignore[attr-defined]
    from fides.api.models.system_manager import SystemManager


class FidesUser(Base):
    """The DB ORM model for FidesUser."""

    username = Column(CIText, unique=True, index=True)
    email_address = Column(CIText, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    salt = Column(String, nullable=True)
    disabled = Column(Boolean, nullable=False, server_default="f")
    disabled_reason = Column(EnumColumn(DisabledReason), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_at = Column(DateTime(timezone=True), nullable=True)
    password_login_enabled = Column(Boolean, nullable=True)
    totp_secret = Column(
        StringEncryptedType(
            type_in=String(),
            key=CONFIG.security.app_encryption_key,
            engine=AesGcmEngine,
            padding="pkcs5",
        ),
        nullable=True,
    )

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
    # permissions relationship is defined via backref in FidesUserPermissions
    email_verifications = relationship(
        "FidesUserRespondentEmailVerification",
        back_populates="user",
        cascade="all,delete",
        lazy="dynamic",
        foreign_keys="[FidesUserRespondentEmailVerification.user_id]",
    )
    permissions = relationship(
        "FidesUserPermissions",
        back_populates="user",
        cascade="all,delete",
        uselist=False,
    )

    # Manual task assignments relationship
    manual_task_references = relationship(
        "ManualTaskReference",
        primaryjoin="and_(FidesUser.id == foreign(ManualTaskReference.reference_id), "
        "ManualTaskReference.reference_type == 'assigned_user')",
        viewonly=True,
    )

    @property
    def system_ids(self) -> List[str]:
        return [system.id for system in self.systems]

    @classmethod
    def hash_password(cls, password: str, encoding: str = "UTF-8") -> tuple[str, str]:
        """Utility function to hash a user's password with a generated salt"""
        salt = generate_salt()
        hashed_password = hash_credential_with_salt(
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
        hashed_password = None
        salt = None

        if password := data.get("password"):
            hashed_password, salt = FidesUser.hash_password(password)

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
                "password_login_enabled": data.get("password_login_enabled"),
            },
            check_name=check_name,
        )

        return user  # type: ignore

    @classmethod
    def create_respondent(cls, db: Session, data: dict[str, Any]) -> FidesUser:
        """Create an external respondent user. This user will not be able to login with a password and
        requires an email address to be provided.
        """
        if not data.get("email_address"):
            raise ValueError("Email address is required for external respondents")
        if data.get("password"):
            raise ValueError("Password login is not allowed for external respondents")
        data["password_login_enabled"] = False
        return cls.create(db, data)

    def credentials_valid(self, password: str, encoding: str = "UTF-8") -> bool:
        """Verifies that the provided password is correct."""
        if self.salt is None:
            return False

        provided_password_hash = hash_credential_with_salt(
            password.encode(encoding),
            self.salt.encode(encoding),
        )

        return provided_password_hash == self.hashed_password

    def update_password(self, db: Session, new_password: str) -> None:
        """Updates the user's password to the specified value.

        No validations are performed on the old/existing password within this function.
        """
        if self.permissions is not None:
            if self.permissions.is_external_respondent():
                raise ValueError(
                    "Password changes are not allowed for external respondents"
                )

        hashed_password, salt = FidesUser.hash_password(new_password)
        self.hashed_password = hashed_password  # type: ignore
        self.salt = salt  # type: ignore
        self.password_reset_at = datetime.utcnow()  # type: ignore
        self.save(db)

    def update_email_address(self, db: Session, new_email_address: str) -> None:
        """Updates the user's email address to the specified value."""
        if self.permissions is not None:
            if self.permissions.is_external_respondent():
                raise ValueError(
                    "Email address changes are not allowed for external respondents"
                )

        self.email_address = new_email_address  # type: ignore
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

        if self.permissions is not None:
            if self.permissions.is_external_respondent():
                raise SystemManagerException(
                    "External respondents cannot be system managers."
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
