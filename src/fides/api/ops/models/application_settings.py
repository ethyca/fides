from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import Boolean, CheckConstraint, Column
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.ops.db.base_class import JSONTypeOverride
from fides.core.config import get_config
from fides.lib.db.base_class import Base

CONFIG = get_config()


class ApplicationSettings(Base):
    """
    Stores application settings, set through different mechanisms, as JSON blobs in the DB.

    This is a single-row table. The single record describes global application settings.
    """

    api_set = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                CONFIG.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=False,
        default={},
    )  # store as encrypted JSON blob since settings may have sensitive data
    single_row = Column(
        Boolean, primary_key=True, default=True
    )  # used to constrain table to one row

    CheckConstraint("single_row", name="single_row_check")

    @classmethod
    def create_or_update(  # type: ignore[override]
        cls, db: Session, *, data: Dict[str, Any]
    ) -> ApplicationSettings:
        """
        Creates the settings record if none exists, or updates the existing record.

        Here we effectively prevent more than a single record in the table.
        """
        existing_record = db.query(cls).first()
        if existing_record:
            updated_record = existing_record.update(db=db, data=data)
            return updated_record

        return cls.create(db=db, data=data)

    def update(self, db: Session, data: Dict[str, Any]) -> ApplicationSettings:  # type: ignore[override]
        """
        Updates the settings record, merging contents of the JSON column
        """
        incoming_settings = data["api_set"]
        if not isinstance(incoming_settings, dict):
            raise ValueError("`api_set` column must be a dictionary")

        # update, i.e. merge, the `api_set` dict
        self.api_set.update(incoming_settings)
        self.save(db=db)
        return self

    @classmethod
    def get_api_set_settings(cls, db: Session) -> Dict[str, Any]:
        """
        Utility method to get the api_set settings dict

        An empty `dict` will be returned if no settings have been set through the API
        """
        settings_record = db.query(cls).first()
        if settings_record:
            return settings_record.api_set
        return {}
