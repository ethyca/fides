from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from fides.api.ops.models.application_config import ApplicationConfig
from fides.api.ops.schemas.storage.storage import StorageType


class ConfigProxyBase:
    """
    Base class that's used to make config proxy classes that correspond
    to our config/settings sub-sections.

    Config proxy classes are a construct to allow for accessing "resolved"
    config properties based on api-set and "traditional" config-set mechanisms.
    Config proxy classes allow these "resolved" properties to be looked up
    as if they were a "normal" pydantic config object, i.e. with dot notation,
    e.g. `ConfigProxy(db).notifications.notification_service_type`
    """

    prefix: str

    def __init__(self, db: Session) -> None:
        self._db = db

    def __getattribute__(self, __name: str) -> Any:
        """
        This allows us to retrieve resolved config properties when
        using the config proxy as a "normal" config object, i.e. with dot notation,
        e.g. `config_proxy.notifications.notification_service_type
        """
        if __name in ("_db", "prefix"):
            return object.__getattribute__(self, __name)
        return ApplicationConfig.get_resolved_config_property(
            self._db, f"{self.prefix}.{__name}"
        )


class NotificationSettingsProxy(ConfigProxyBase):
    prefix = "notifications"

    send_request_completion_notification: bool
    send_request_receipt_notification: bool
    send_request_review_notification: bool
    notification_service_type: Optional[str]


class ExecutionSettingsProxy(ConfigProxyBase):
    prefix = "execution"

    subject_identity_verification_required: bool
    require_manual_request_approval: bool


class StorageSettingsProxy(ConfigProxyBase):
    prefix = "storage"

    active_default_storage_type: StorageType


class ConfigProxy:
    """
    ConfigProxy instances allow access to "resolved" config properties
    based on resolution between api-set and "traditional" config-set mechanisms.
    ConfigProxy instances allow these "resolved" properties to be looked up
    as if they were a "normal" pydantic config object, i.e. with dot notation,
    e.g. `ConfigProxy(db).notifications.notification_service_type`

    To instantiate a `ConfigProxy`, you must have an active db `Session`,
    since the `ConfigProxy` will rely on the db for property resolution.

    Instantiating a `ConfigProxy` is itself a cheap operation,
    i.e. there is minimal resource overhead with instantiating a new `ConfigProxy`.
    The `ConfigProxy` is a thin wrapper above the given db `Session` -
    it relies on the given db `Session` and for all of its state.

    Lookups (i.e. attribute access) with the `ConfigProxy` do leverage
    the underlying ORM model, but any db calls that are needed should be straightforward -
    it leverages only a fixed single-row table holding the config state.
    """

    def __init__(self, db: Session) -> None:
        self.notifications = NotificationSettingsProxy(db)
        self.execution = ExecutionSettingsProxy(db)
        self.storage = StorageSettingsProxy(db)
