from typing import Any, Dict

from sqlalchemy import Boolean, CheckConstraint, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base, FidesBase

default_privacy_center_config = {
    "actions": [
        {
            "policy_key": "default_access_policy",
            "title": "Access your data",
            "identity_inputs": {"email": "required"},
        },
        {
            "policy_key": "default_erasure_policy",
            "title": "Erase your data",
            "identity_inputs": {"email": "required"},
        },
    ],
}


class PrivacyCenterConfig(Base):
    """
    A single-row table used to store the subset of the Privacy Center's config.json that is supported by the Admin UI.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "plus_privacy_center_config"

    config = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
    )
    single_row = Column(
        Boolean,
        default=True,
        nullable=False,
        unique=True,
    )  # used to constrain table to one row

    CheckConstraint("single_row", name="plus_privacy_center_config_single_row_check")
    UniqueConstraint("single_row", name="plus_privacy_center_config_single_row_unique")

    @classmethod
    def create_or_update(  # type: ignore[override]
        cls,
        db: Session,
        *,
        data: Dict[str, Any],
    ) -> FidesBase:
        """
        Creates a new config record if one doesn't exist, or updates the existing record.

        Here we effectively prevent more than a single record in the table.
        """
        existing_record = db.query(cls).first()
        if existing_record:
            updated_record = existing_record.update(
                db=db,
                data=data,
            )  # type: ignore[arg-type]
            return updated_record

        return cls.create(db=db, data=data)
