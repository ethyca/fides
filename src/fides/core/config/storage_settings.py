from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import root_validator

from fides.api.ops.schemas.storage.storage import (
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

    class Config:
        env_prefix = ENV_PREFIX
