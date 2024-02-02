from __future__ import annotations

from json import loads
from typing import Any, Dict, Iterable, Optional

from loguru import logger
from pydantic.utils import deep_update
from pydash.objects import get
from sqlalchemy import Boolean, CheckConstraint, Column
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.db.base_class import Base, JSONTypeOverride
from fides.config import CONFIG, FidesConfig


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
    config_set = Column(
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
        cls,
        db: Session,
        *,
        data: Dict[str, Any],
        merge_updates: bool = True,
    ) -> ApplicationConfig:
        """
        Creates the config record if none exists, or updates the existing record.

        Here we effectively prevent more than a single record in the table.
        """
        existing_record = db.query(cls).first()
        if existing_record:
            updated_record = existing_record.update(
                db=db, data=data, merge_updates=merge_updates
            )
            return updated_record

        return cls.create(db=db, data=data)

    def update(self, db: Session, data: Dict[str, Any], merge_updates: bool = True) -> ApplicationConfig:  # type: ignore[override]
        """
        Updates the config record, merging contents of the particular JSON column that
        corresponds to the updated data.

        Given `data` dict should have either/both an `api_set` and/or `config_set` key at the top-level.
        Those keys will then point to `dict`s of data to update, i.e. merge, with the existing contents
        of the `api_set` or `config_set` columns, respectively.
        """
        if "api_set" in data:
            incoming_api_config = data["api_set"]
            if not isinstance(incoming_api_config, dict):
                raise ValueError("`api_set` column must be a dictionary")

            if merge_updates:
                # merge, the `api_set` dict
                self.api_set = deep_update(self.api_set, incoming_api_config)
            else:
                # replace the `api_set` dict
                self.api_set = incoming_api_config

        if "config_set" in data:
            incoming_config_config = data["config_set"]
            if not isinstance(incoming_config_config, dict):
                raise ValueError("`config_set` column must be a dictionary")

            if merge_updates:
                # update, i.e. merge, the `config_set` dict
                self.config_set = deep_update(self.config_set, incoming_config_config)
            else:
                self.config_set = incoming_config_config

        self.save(db=db)
        return self

    @classmethod
    def get_api_set(cls, db: Session) -> Dict[str, Any]:
        """
        Utility method to get the api_set config settings dict

        An empty `dict` will be returned if no config settings have been set through the API
        """
        config_record = db.query(cls).first()
        if config_record:
            return config_record.api_set
        return {}

    @classmethod
    def get_config_set(cls, db: Session) -> Dict[str, Any]:
        """
        Utility method to get the config_set config dict

        An empty `dict` will be returned if no config settings have been set through config
        """
        config_record = db.query(cls).first()
        if config_record:
            return config_record.config_set
        return {}

    @classmethod
    def update_api_set(
        cls,
        db: Session,
        api_set_dict: Dict[str, Any],
        merge_updates: bool = True,
    ) -> ApplicationConfig:
        """
        Utility method to set the `api_set` column on the `applicationconfig`
        db record with the provided dictionary of data.

        Depending on `merge_updates` param, updates either:
         - are *merged* with any existing `api_set` data in the db
         - replace any existing `api_set` data in the db
        """
        return cls.create_or_update(
            db, data={"api_set": api_set_dict}, merge_updates=merge_updates
        )

    @classmethod
    def clear_api_set(cls, db: Session) -> Optional[ApplicationConfig]:
        """
        Utility method to set the `api_set` column on the `applicationconfig`
        db record to an empty dict

        """
        existing_record = db.query(cls).first()
        if existing_record:
            existing_record.api_set = {}
            existing_record.save(db)
            return existing_record
        return None

    @classmethod
    def clear_config_set(cls, db: Session) -> Optional[ApplicationConfig]:
        """
        Utility method to set the `config_set` column on the `applicationconfig`
        db record to an empty dict

        """
        existing_record = db.query(cls).first()
        if existing_record:
            existing_record.config_set = {}
            existing_record.save(db)
            return existing_record
        return None

    @classmethod
    def update_config_set(cls, db: Session, config: FidesConfig) -> ApplicationConfig:
        """
        Utility method to set the `config_set` column on the `applicationconfig`
        db record by serializing the given `FidesConfig` to a JSON blob.
        """
        # need to do this deserialization round-trip to get us a dict
        # that's serializable as JSON in the db:
        # pydantic's `.dict()` is NOT serializable as JSON --
        # see https://github.com/pydantic/pydantic/issues/1409
        config_dict = loads(config.json())
        return cls.create_or_update(db, data={"config_set": config_dict})

    @classmethod
    def get_resolved_config_property(
        cls,
        db: Session,
        config_property: str,
        merge_values: bool = False,
        default_value: Any = None,
    ) -> Optional[Any]:
        """
        Gets the 'resolved' config property based on api-set and config-set configs.
        `config_property` is a dot-separated path to the config property,
        e.g. `notifications.notification_service_type`.

        Api-set values get priority over config-set, in case of conflict, unless `merge_values`
        is specified as `True`, in which case the proxy will attempt to _merge_ the api-set
        and config-set values. Note that only iterable config values (e.g. lists) can be merged!

        An error will be thrown if `merge_values` is used for a property with non-iterable values.
        """
        config_record = db.query(cls).first()
        if config_record:
            api_prop = get(config_record.api_set, config_property)
            config_prop = get(config_record.config_set, config_property, default_value)
            # if no api-set property found, fall back to config-set
            if api_prop is None:
                return config_prop

            # if we want to merge values and have a config property too
            if merge_values and config_prop is not None:
                # AND we have iterable api and config-set properties, then we try to merge
                if not isinstance(api_prop, Iterable) or not isinstance(
                    config_prop, Iterable
                ):
                    raise RuntimeError("Only iterable values can be merged!")
                return {value for value in (list(api_prop) + list(config_prop))}

            # otherwise, we just use the api-set property
            return api_prop

        logger.warning("No config record found!")
        return default_value
