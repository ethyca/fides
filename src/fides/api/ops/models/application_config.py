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


class ApplicationConfig(Base):
    """
    Stores application config settings, set through different mechanisms, as JSON blobs in the DB.

    This is a single-row table. The single record describes global application config settings.
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
    )  # store as encrypted JSON blob since config settings may have sensitive data
    single_row = Column(
        Boolean, default=True, nullable=False
    )  # used to constrain table to one row

    CheckConstraint("single_row", name="single_row_check")

    @classmethod
    def create_or_update(  # type: ignore[override]
        cls, db: Session, *, data: Dict[str, Any]
    ) -> ApplicationConfig:
        """
        Creates the config record if none exists, or updates the existing record.

        Here we effectively prevent more than a single record in the table.
        """
        existing_record = db.query(cls).first()
        if existing_record:
            updated_record = existing_record.update(db=db, data=data)
            return updated_record

        return cls.create(db=db, data=data)

    def update(self, db: Session, data: Dict[str, Any]) -> ApplicationConfig:  # type: ignore[override]
        """
        Updates the config record, merging contents of the JSON column
        """
        incoming_config = data["api_set"]
        if not isinstance(incoming_config, dict):
            raise ValueError("`api_set` column must be a dictionary")

        # update, i.e. merge, the `api_set` dict
        self.api_set.update(incoming_config)
        self.save(db=db)
        return self

    @classmethod
    def get_api_set_config(cls, db: Session) -> Dict[str, Any]:
        """
        Utility method to get the api_set config settings dict

        An empty `dict` will be returned if no config settings have been set through the API
        """
        config_record = db.query(cls).first()
        if config_record:
            return config_record.api_set
        return {}
