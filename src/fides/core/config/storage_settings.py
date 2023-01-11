from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import root_validator

from fides.api.ops.schemas.storage.storage import (
    DEFAULT_STORAGE_KEY,
    SUPPORTED_STORAGE_SECRETS,
    FileNaming,
    ResponseFormat,
    S3AuthMethod,
    StorageDestination,
    StorageType,
)
from fides.api.ops.util.storage_util import get_schema_for_secrets

from .fides_settings import FidesSettings

ENV_PREFIX = "FIDES__STORAGE__"

BASE_FIELDS_MAPPING = {
    "default_storage_type": "type",
    "default_storage_format": "format",
}

DETAILS_FIELDS_MAPPING = {
    "default_storage_naming": "naming",
    "default_storage_s3_auth_method": "auth_method",
    "default_storage_s3_bucket": "bucket",
    "default_storage_s3_max_retries": "max_retries",
}

SECRETS_FIELDS_MAPPING = {
    "default_storage_secrets_aws_access_key_id": "aws_access_key_id",
    "default_storage_secrets_aws_secret_access_key": "aws_secret_access_key",
}

S3_SPECIFIC_DETAIL_FIELDS = [
    "default_storage_s3_auth_method",
    "default_storage_s3_bucket",
    "default_storage_s3_max_retries",
]
S3_SPECIFIC_SECRETS_FIELDS = [
    "default_storage_secrets_aws_access_key_id",
    "default_storage_secrets_aws_secret_access_key",
]
S3_SPECIFIC_FIELDS = S3_SPECIFIC_DETAIL_FIELDS + S3_SPECIFIC_SECRETS_FIELDS


class StorageSettings(FidesSettings):
    """Configuration settings for the default storage configuration"""

    default_storage_type: StorageType = StorageType.local
    default_storage_naming: FileNaming = FileNaming.request_id
    default_storage_format: ResponseFormat = ResponseFormat.json

    # s3-only details
    default_storage_s3_auth_method: Optional[S3AuthMethod] = None
    default_storage_s3_bucket: Optional[str] = None
    default_storage_s3_max_retries: Optional[int] = None

    # secrets
    default_storage_secrets_aws_access_key_id: Optional[str] = None
    default_storage_secrets_aws_secret_access_key: Optional[str] = None

    default_storage_destination: Optional[StorageDestination] = None
    default_storage_secrets: Optional[SUPPORTED_STORAGE_SECRETS] = None

    @root_validator
    @classmethod
    def validate_storage_details_and_secrets(
        cls: type[StorageSettings], values: Dict[str, Any]
    ) -> Optional[str]:
        """Ensure the provided storage configs are appropriate for the given storage type"""
        # we go through the process of creating our default storage destination
        # to validate that the provided config values can be parsed appropriately
        cls.default_storage_destination = cls.default_storage_destination_from_config(
            values
        )
        print(cls.default_storage_destination)

        # similarly, we go through the process of creating a secrets object
        # as a validation step, iff we're using the s3 `secret_keys` auth method
        if (
            "default_storage_s3_auth_method" in values.keys()
            and values["default_storage_s3_auth_method"] == S3AuthMethod.SECRET_KEYS
        ):
            cls.default_storage_secrets = cls.default_storage_secrets_from_config(
                values
            )

        # # raise a validation error if we've got s3-specific fields
        # # defined while using a non-s3 default storage type
        # if storage_type is not StorageType.s3:
        #     incorrect_s3_fields = [
        #         s3_field for s3_field in S3_SPECIFIC_FIELDS if s3_field in values.keys()
        #     ]
        #     if incorrect_s3_fields:
        #         raise ValueError(
        #             f"The configuration properties {incorrect_s3_fields} can only be used if an `s3` default storage type is configured"
        #         )

        # if (
        #     storage_type is StorageType.s3
        #     and values["default_storage_s3_auth_method"] is not S3AuthMethod.SECRET_KEYS
        # ):
        #     incorrect_s3_secrets_fields = [
        #         s3_field
        #         for s3_field in S3_SPECIFIC_SECRETS_FIELDS
        #         if s3_field in values.keys()
        #     ]
        #     if incorrect_s3_secrets_fields:
        #         raise ValueError(
        #             f"The configuration properties {incorrect_s3_secrets_fields} can only be used with the `secret_keys` auth method"
        #         )

        return values

    class Config:
        env_prefix = ENV_PREFIX

    @classmethod
    def default_storage_destination_from_config(
        cls: type[StorageSettings], config_values: Dict[str, Any]
    ) -> StorageDestination:
        # this will hold the "payload" to seed the StorageDestination
        destination_config = {}
        destination_config["details"] = {}

        # first we fill in our constants for the default
        destination_config["name"] = "Default Storage Config"
        destination_config["key"] = DEFAULT_STORAGE_KEY
        destination_config["is_default"] = True

        # then we translate the provided config values to fill in the payload
        for config_field, config_value in config_values.items():
            if config_value:
                if isinstance(config_value, Enum):
                    config_value = config_value.value
                if config_field in BASE_FIELDS_MAPPING:
                    destination_config[BASE_FIELDS_MAPPING[config_field]] = config_value
                elif config_field in DETAILS_FIELDS_MAPPING:
                    destination_config["details"][
                        DETAILS_FIELDS_MAPPING[config_field]
                    ] = config_value
        # then we actually create our StorageDestination object
        # this includes validation
        return StorageDestination(**destination_config)

    @classmethod
    def default_storage_secrets_from_config(
        cls: type[StorageSettings], config_values: Dict[str, Any]
    ) -> StorageDestination:
        # this will hold the "payload" to seed the secrets
        secrets_config = {}

        # then we translate the provided config values to fill in the payload
        for config_field, config_value in config_values.items():
            if config_value:
                if isinstance(config_value, Enum):
                    config_value = config_value.value
                if config_field in SECRETS_FIELDS_MAPPING:
                    secrets_config[SECRETS_FIELDS_MAPPING[config_field]] = config_value

        # then we actually create our secrets object
        # this includes validation
        storage_type = config_values["default_storage_type"]
        return get_schema_for_secrets(storage_type=storage_type, secrets=secrets_config)
