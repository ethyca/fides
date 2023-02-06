from __future__ import annotations

from typing import Any, Dict

from pydantic import Extra, root_validator

from fides.lib.schemas.base_class import BaseSchema

ACTIVE_DEFAULT_STORAGE_PROPERTY = "fides.storage.active_default_storage_type"
ACTIVE_DEFAULT_STORAGE_ALLOWED_VALUES = ("local", "s3")

ALLOWED_SETTINGS_KEYS = ACTIVE_DEFAULT_STORAGE_PROPERTY


class ApplicationSettings(BaseSchema):
    """
    Application settings update body is an arbitrary dict (JSON object)
    We describe it in a schema to enforce some restrictions on the keys passed.

    TODO: Eventually this should be driven by a more formal validation schema for this
    the application settings that is properly hooked up to the global pydantic config module.
    """

    class Config:
        extra = Extra.allow

    @root_validator
    @classmethod
    def validate_settings_fields(  # type: ignore
        cls: ApplicationSettings, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        prohibited_keys = [
            key for key in values.keys() if key not in ALLOWED_SETTINGS_KEYS
        ]
        if prohibited_keys:
            raise ValueError(
                f"Prohibited settings key(s) found: [{prohibited_keys}]. Allowed settings keys are: [{ALLOWED_SETTINGS_KEYS}]"
            )

        if ACTIVE_DEFAULT_STORAGE_PROPERTY in values:
            validate_active_default_storage_type(
                values[ACTIVE_DEFAULT_STORAGE_PROPERTY]
            )
        return values


class ApplicationSettingsUpdate(ApplicationSettings):
    """
    Extension to base schema to ensure that update payloads are not empty
    """

    @root_validator
    @classmethod
    def validate_settings_fields_not_empty(  # type: ignore
        cls: ApplicationSettings, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not values:
            raise ValueError("A settings object must be provided.")
        return values


def validate_active_default_storage_type(value: Any) -> None:
    """
    Validation function for values of the "active default storage" application property.

    TODO: Eventually this should be driven by a more formal validation schema for this
    the application settings that is properly hooked up to the global pydantic config module.
    """
    if not isinstance(value, str):
        raise ValueError(f"{ACTIVE_DEFAULT_STORAGE_PROPERTY} setting must be a string")
    if value not in ACTIVE_DEFAULT_STORAGE_ALLOWED_VALUES:
        raise ValueError(
            f"{ACTIVE_DEFAULT_STORAGE_PROPERTY} setting must be one of the allowed values: [{ACTIVE_DEFAULT_STORAGE_ALLOWED_VALUES}]"
        )
