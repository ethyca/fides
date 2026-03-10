from sqlalchemy import Boolean, CheckConstraint, Column, UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import (
    Base,  # type: ignore[attr-defined]
    JSONTypeOverride,
)
from fides.api.db.encryption_utils import encrypted_type


class IdentitySalt(Base):
    """
    A single-row table used to store the encrypted salt value used for identity hashing (SHA-256).
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "identity_salt"

    encrypted_value = Column(
        MutableDict.as_mutable(encrypted_type(type_in=JSONTypeOverride)),
        nullable=True,
    )  # Type bytea in the db
    single_row = Column(
        Boolean,
        default=True,
        nullable=False,
        unique=True,
    )  # used to constrain table to one row

    CheckConstraint("single_row", name="identity_salt_single_row_check")
    UniqueConstraint("single_row", name="identity_salt_single_row_unique")
