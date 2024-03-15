from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional, Set

from fastapi.applications import FastAPI
from pydantic import AnyUrl
from sqlalchemy.orm import Session

from fides.api.models.application_config import ApplicationConfig
from fides.api.schemas.storage.storage import StorageType
from fides.api.util.cors_middleware_utils import update_cors_middleware
from fides.config import CONFIG


def merge_properties(attribute_names: Iterable[str]) -> Callable:
    """
    Decorator to specify a config proxy class's attributes as config properties
    whose api-set and config-set values should be _merged_ when resolved by the proxy.
    """

    def decorator(cls: ConfigProxyBase) -> ConfigProxyBase:
        cls.merge_properties = set(attribute_names)
        return cls

    return decorator


class ConfigProxyBase:
    """
    Base class that's used to make config proxy classes that correspond
    to our config/settings sub-sections.

    Config proxy classes are a construct to allow for accessing "resolved"
    config properties based on api-set and "traditional" config-set mechanisms.
    Config proxy classes allow these "resolved" properties to be looked up
    as if they were a "normal" pydantic config object, i.e. with dot notation,
    e.g. `ConfigProxy(db).notifications.notification_service_type`

    Merging: to have a given config property's api-set and config-set values to be merged
    on property resolution, use the `@merge_properties` decorator on the config proxy
    class to specify the corresponding attribute name.

    For example, if creating a config proxy class:
    ```
    @merge_properties(["cors_origins"])
    class SecuritySettingsProxy(ConfigProxyBase):
        prefix = "security"
        cors_origins: List[str]
    ```

    and `security.cors_origins` has the following values:
    config-set: `["a", "b"]`
    api-set: `["b", "c"]`

    then, when using the config proxy to access the attribute, it will return
    a merged set of values:
    ```
    >>> ConfigProxy(db).security.cors_origins
    {"a", "b", "c"}
    ```

    """

    prefix: str
    merge_properties: Set[str] = set()

    def __init__(self, db: Session) -> None:
        self._db = db

    def __getattribute__(self, __name: str) -> Any:
        """
        This allows us to retrieve resolved config properties when
        using the config proxy as a "normal" config object, i.e. with dot notation,
        e.g. `config_proxy.notifications.notification_service_type
        """
        if __name in ("_db", "merge_properties", "prefix"):
            return object.__getattribute__(self, __name)
        return ApplicationConfig.get_resolved_config_property(
            self._db,
            f"{self.prefix}.{__name}",
            merge_values=__name in self.merge_properties,
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
    disable_consent_identity_verification: bool
    require_manual_request_approval: bool

    def __getattribute__(self, name: str) -> Any:
        """
        Overrides base __getattribute__ to provide a dynamic fallback for
        'disable_consent_identity_verification'. The fallback is based on
        'subject_identity_verification_required' only when no explicit value is provided,
        preserving None for unset cases.
        """
        if name == "disable_consent_identity_verification":
            value = super().__getattribute__("disable_consent_identity_verification")
            if value is None:
                subject_verification_required = super().__getattribute__(
                    "subject_identity_verification_required"
                )
                return not subject_verification_required
            return value

        return super().__getattribute__(name)


class StorageSettingsProxy(ConfigProxyBase):
    prefix = "storage"

    active_default_storage_type: StorageType


@merge_properties(["cors_origins"])
class SecuritySettingsProxy(ConfigProxyBase):
    prefix = "security"

    # only valid URLs should be set as cors_origins
    # for advanced usage of non-URLs, e.g. wildcards (`*`), the related
    # `cors_origin_regex` property should be used.
    # this is explicitly _not_ accessible via API - it must be used with care.
    cors_origins: List[AnyUrl]


class ConsentSettingsProxy(ConfigProxyBase):
    prefix = "consent"

    override_vendor_purposes: bool


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
        self.security = SecuritySettingsProxy(db)
        self.consent = ConsentSettingsProxy(db)

    def load_current_cors_domains_into_middleware(self, app: FastAPI) -> None:
        """
        Util function that loads the current CORS domains from
        `ConfigProxy` into the  `CORSMiddleware` at runtime.
        """

        # NOTE: `cors_origins` config proxy resolution _merges_ api-set and config-set values, if both present
        current_config_proxy_domains = (
            self.security.cors_origins if self.security.cors_origins is not None else []
        )

        update_cors_middleware(
            app,
            current_config_proxy_domains,
            CONFIG.security.cors_origin_regex,
        )
