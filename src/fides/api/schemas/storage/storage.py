from enum import Enum
from typing import Any, Dict, List, Optional, Union

from fideslang.validation import FidesKey
from pydantic import (
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic.main import BaseModel

from fides.api.schemas.api import BulkResponse, BulkUpdateFailed


class ResponseFormat(Enum):
    """Response formats"""

    json = "json"
    csv = "csv"
    html = "html"


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
    ENABLE_STREAMING = "enable_streaming"
    ENABLE_ACCESS_PACKAGE_REDIRECT = "enable_access_package_redirect"
    model_config = ConfigDict(extra="forbid")


class FileBasedStorageDetails(BaseModel):
    """A base class for all storage configuration that uses a file system."""

    naming: str = FileNaming.request_id.value  # How to name the uploaded file
    model_config = ConfigDict(extra="forbid")


class AWSAuthMethod(str, Enum):
    AUTOMATIC = "automatic"
    SECRET_KEYS = "secret_keys"


class StorageDetailsS3(FileBasedStorageDetails):
    """The details required to represent an AWS S3 storage bucket."""

    auth_method: AWSAuthMethod
    bucket: str
    max_retries: Optional[int] = 0
    enable_streaming: Optional[bool] = False
    enable_access_package_redirect: Optional[bool] = False
    model_config = ConfigDict(use_enum_values=True)


class GCSAuthMethod(str, Enum):
    ADC = "adc"  # Application Default Credentials
    SERVICE_ACCOUNT_KEYS = "service_account_keys"


class StorageDetailsGCS(FileBasedStorageDetails):
    """The details required to represent a Google Cloud Storage bucket."""

    auth_method: GCSAuthMethod
    bucket: str
    max_retries: Optional[int] = 0
    model_config = ConfigDict(use_enum_values=True)


class StorageDetailsLocal(FileBasedStorageDetails):
    """The details required to configurate local storage configuration"""


class StorageSecrets(Enum):
    """Enum for storage secret keys"""

    # s3-specific
    AWS_ACCESS_KEY_ID = "aws_access_key_id"
    AWS_SECRET_ACCESS_KEY = "aws_secret_access_key"
    REGION_NAME = "region_name"
    AWS_ASSUME_ROLE = "assume_role_arn"


class StorageSecretsLocal(BaseModel):
    """A dummy schema for allowing any / no secrets for local filestorage."""

    model_config = ConfigDict(extra="allow")


class StorageSecretsS3(BaseModel):
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: Optional[str] = None
    assume_role_arn: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class StorageSecretsGCS(BaseModel):
    """The secrets required to connect to a Google Cloud Storage bucket."""

    type: str = "service_account"
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
    universe_domain: str
    model_config = ConfigDict(extra="forbid")


class StorageType(Enum):
    """Enum for storage destination types"""

    s3 = "s3"
    gcs = "gcs"
    transcend = "transcend"
    ethyca = "ethyca"
    local = "local"  # local should be used for testing only, not for processing real-world privacy requests


FULLY_CONFIGURED_STORAGE_TYPES = (
    StorageType.s3,
    StorageType.gcs,
)  # storage types that are considered "fully configured"


class StorageDestinationBase(BaseModel):
    """Storage Destination Schema -- used for setting defaults"""

    type: StorageType
    details: Union[
        StorageDetailsS3,
        StorageDetailsGCS,
        StorageDetailsLocal,
    ] = Field(validate_default=True)
    format: Optional[ResponseFormat] = ResponseFormat.json.value  # type: ignore
    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, extra="forbid"
    )

    @field_validator("details", mode="before")
    @classmethod
    def validate_details_validator(
        cls,
        v: Dict[str, str],
        info: ValidationInfo,
    ) -> Dict[str, str]:
        """
        Custom validation logic for the `details` field.
        """
        storage_type = info.data.get("type")
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
                StorageType.gcs.value: StorageDetailsGCS,
                StorageType.local.value: StorageDetailsLocal,
            }[storage_type]
        except KeyError:
            raise ValueError(
                f"`storage_type` {storage_type} has no supported `details` validation."
            )
        try:
            schema.model_validate(details)  # type: ignore
        except ValidationError as exc:
            # Pydantic requires validators raise either a ValueError, TypeError, or AssertionError
            # so this exception is cast into a `ValueError`.
            errors = [f"{err['msg']} {str(err['loc'])}" for err in exc.errors()]
            raise ValueError(errors)

        return details

    @model_validator(mode="after")
    def format_validator(self) -> "StorageDestinationBase":
        """
        Custom validation to ensure that local destination formats are valid.
        """
        restricted_destinations = [StorageType.local.value]
        storage_type = self.type
        response_format = self.format
        if (
            storage_type in restricted_destinations
            and response_format
            and response_format
            not in [ResponseFormat.json.value, ResponseFormat.html.value]
        ):
            raise ValueError(
                "Only JSON or HTML upload format are supported for local storage destinations."
            )

        return self


class StorageDestination(StorageDestinationBase):
    """Storage Destination Schema"""

    name: str
    key: Optional[FidesKey] = None
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


class StorageDestinationResponse(BaseModel):
    """Storage Destination Response Schema"""

    name: str
    type: StorageType
    details: Dict[StorageDetails, Any]
    key: FidesKey
    format: ResponseFormat
    is_default: bool = False
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class BulkPutStorageConfigResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of StorageConfig."""

    succeeded: List[StorageDestinationResponse] = []
    failed: List[BulkUpdateFailed] = []


SUPPORTED_STORAGE_SECRETS = Union[StorageSecretsS3, StorageSecretsGCS]


class StorageConfigStatus(Enum):
    """Enum for configuration statuses of a storage config"""

    configured = "configured"
    not_configured = "not configured"


class StorageConfigStatusMessage(BaseModel):
    """A schema for checking configuration status of storage config."""

    config_status: Optional[StorageConfigStatus] = None
    detail: Optional[str] = None
