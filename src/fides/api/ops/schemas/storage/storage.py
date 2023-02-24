from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fideslang.validation import FidesKey
from pydantic import Extra, ValidationError, root_validator, validator
from pydantic.main import BaseModel
from validators.url import regex

from fides.api.ops.schemas.api import BulkResponse, BulkUpdateFailed


class DownloadFormat(Enum):
    """Download formats for DSR packages"""

    json = "json"
    csv = "csv"


class FileNaming(Enum):
    """File naming options for data uploads"""

    request_id = "request_id"


class StorageDetails(Enum):
    """Enum for storage detail keys"""

    # s3-specific
    BUCKET = "bucket"
    NAMING = "naming"
    MAX_RETRIES = "max_retries"
    AUTH_METHOD = "auth_method"

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class HtmlLandingPageProps(Enum):
    """Enum for Html Landing Page props"""

    LOGO_PATH = "logo_path"

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class FileBasedStorageDetails(BaseModel):
    """A base class for all storage configuration that uses a file system."""

    naming: str = FileNaming.request_id.value  # How to name the uploaded file

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class S3AuthMethod(Enum):
    AUTOMATIC = "automatic"
    SECRET_KEYS = "secret_keys"


class StorageDetailsS3(FileBasedStorageDetails):
    """The details required to represent an AWS S3 storage bucket."""

    auth_method: S3AuthMethod
    bucket: str
    max_retries: Optional[int] = 0

    class Config:
        use_enum_values = True


class StorageDetailsLocal(FileBasedStorageDetails):
    """The details required to configurate local storage configuration"""


class StorageSecrets(Enum):
    """Enum for storage secret keys"""

    # s3-specific
    AWS_ACCESS_KEY_ID = "aws_access_key_id"
    AWS_SECRET_ACCESS_KEY = "aws_secret_access_key"


class StorageSecretsLocal(BaseModel):
    """A dummy schema for allowing any / no secrets for local filestorage."""

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.allow


class StorageSecretsS3(BaseModel):
    """The secrets required to connect to an S3 bucket."""

    aws_access_key_id: str
    aws_secret_access_key: str

    class Config:
        """Restrict adding other fields through this schema."""

        extra = Extra.forbid


class StorageType(Enum):
    """Enum for storage destination types"""

    s3 = "s3"
    gcs = "gcs"
    transcend = "transcend"
    ethyca = "ethyca"
    local = "local"  # local should be used for testing only, not for processing real-world privacy requests


FULLY_CONFIGURED_STORAGE_TYPES = (
    StorageType.s3,
)  # storage types that are considered "fully configured"


class HtmlLandingPage(BaseModel):
    """HTML Landing Page Schema"""

    logo_path: Optional[str] = None

    @validator("logo_path")
    @classmethod
    def validate_logo_path(cls, value: str) -> str:
        """
        Custom validation logic for the `logo_path` field.
        Should be formatted like `path/to/logo.png`.
        """
        if value:
            pattern = regex(r"(\/.*?\.[\w:]+)")
            if not pattern.search(value):
                raise ValueError("Invalid logo path. Logo path must be formatted like the following: `path/to/logo.png`")
        return value


class StorageDestinationBase(BaseModel):
    """Storage Destination Schema -- used for setting defaults"""

    type: StorageType
    details: Union[
        StorageDetailsS3,
        StorageDetailsLocal,
    ]
    download_format: Optional[DownloadFormat] = DownloadFormat.json.value  # type: ignore
    html_landing_page: Optional[HtmlLandingPage] = None

    class Config:
        use_enum_values = True
        orm_mode = True
        extra = Extra.forbid

    @root_validator(pre=True)
    def maintain_backwards_compatibility(cls, values: Dict) -> Dict:
        """Ensures backwards compatibility after renaming `format` -> `download_format`"""
        if values.get("format"):
            values["download_format"] = values.get("format")
            del values["format"]
        return values

    @validator("details", pre=True, always=True)
    @classmethod
    def validate_details_validator(
        cls,
        v: Dict[str, str],
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Custom validation logic for the `details` field.
        """
        storage_type = values.get("type")
        if not storage_type:
            raise ValueError("A `type` field must be specified.")

        return cls.validate_details(v, storage_type)

    @classmethod
    def validate_details(
        cls,
        details: Dict[str, str],
        storage_type: str,
    ) -> Dict[str, str]:
        """
        Validates the provided storage details field given the storage type.

        Abstracts out the pydantic input parameters to make the validation logic more reusable.
        """
        try:
            schema = {
                StorageType.s3.value: StorageDetailsS3,
                StorageType.local.value: StorageDetailsLocal,
            }[storage_type]
        except KeyError:
            raise ValueError(
                f"`storage_type` {storage_type} has no supported `details` validation."
            )
        try:
            schema.parse_obj(details)  # type: ignore
        except ValidationError as exc:
            # Pydantic requires validators raise either a ValueError, TypeError, or AssertionError
            # so this exception is cast into a `ValueError`.
            errors = [f"{err['msg']} {str(err['loc'])}" for err in exc.errors()]
            raise ValueError(errors)

        return details

    @root_validator
    @classmethod
    def json_validator(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Custom validation to ensure that local destination formats are valid.
        """
        json_only_destinations = [StorageType.local.value]
        storage_type = values.get("type")
        download_format = values.get("download_format")
        if (
            storage_type in json_only_destinations
            and download_format
            and download_format != DownloadFormat.json.value
        ):
            raise ValueError(
                "Only JSON upload format is supported for local storage destinations."
            )

        return values


class StorageDestination(StorageDestinationBase):
    """Storage Destination Schema"""

    name: str
    key: Optional[FidesKey]

    class Config:
        use_enum_values = True
        orm_mode = True


class StorageDestinationResponse(BaseModel):
    """Storage Destination Response Schema"""

    name: str
    type: StorageType
    details: Dict[StorageDetails, Any]
    key: FidesKey
    download_format: DownloadFormat
    html_landing_page: Dict[HtmlLandingPageProps, Any]
    is_default: bool = False

    class Config:
        orm_mode = True
        use_enum_values = True


class BulkPutStorageConfigResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of StorageConfig."""

    succeeded: List[StorageDestinationResponse]
    failed: List[BulkUpdateFailed]


SUPPORTED_STORAGE_SECRETS = StorageSecretsS3


class StorageConfigStatus(Enum):
    """Enum for configuration statuses of a storage config"""

    configured = "configured"
    not_configured = "not configured"


class StorageConfigStatusMessage(BaseModel):
    """A schema for checking configuration status of storage config."""

    config_status: Optional[StorageConfigStatus] = None
    detail: Optional[str] = None
