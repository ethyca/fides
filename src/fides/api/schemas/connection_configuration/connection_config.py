from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from fideslang.models import Dataset
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import BaseModel, ConfigDict, model_validator

from fides.api.common_exceptions import NoSuchConnectionTypeSecretSchemaError
from fides.api.models.connectionconfig import AccessLevel, ConnectionType
from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.saas_config import SaaSConfigBase
from fides.api.util.connection_type import get_connection_type_secret_schema
from fides.api.util.masking_util import mask_sensitive_fields


class CreateConnectionConfiguration(BaseModel):
    """
    Schema for creating a ConnectionConfiguration

    Note that secrets are *NOT* allowed to be supplied here.
    """

    name: Optional[str] = None
    key: Optional[FidesKey] = None
    connection_type: ConnectionType
    access: AccessLevel
    disabled: Optional[bool] = False
    description: Optional[str] = None
    model_config = ConfigDict(
        from_attributes=True, use_enum_values=True, extra="ignore"
    )


class CreateConnectionConfigurationWithSecrets(CreateConnectionConfiguration):
    """Schema for creating a connection configuration including secrets."""

    secrets: Optional[connection_secrets_schemas] = None
    saas_connector_type: Optional[str] = None
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ConnectionConfigSecretsMixin(BaseModel):
    """
    A schema mixin to declare a connection config `secrets` attribute
    and handle masking of sensitive values based on `connection_type`
    and (optionally) a `saas_config`.
    """

    connection_type: ConnectionType
    secrets: Optional[Dict[str, Any]] = None
    saas_config: Optional[SaaSConfigBase] = None

    @model_validator(mode="after")
    def mask_sensitive_values(self) -> "ConnectionConfigSecretsMixin":
        """
        Mask sensitive values in the `secrets` attribute based on `connection_type`
        and (optionally) a `saas_config`.
        """
        if self.secrets is None:
            return self

        connection_type = (
            self.saas_config.type
            if self.connection_type == ConnectionType.saas and self.saas_config
            else self.connection_type.value  # type: ignore
        )
        try:
            secret_schema = get_connection_type_secret_schema(
                connection_type=connection_type
            )
        except NoSuchConnectionTypeSecretSchemaError as e:
            logger.error(e)
            # if there is no schema, we don't know what values to mask.
            # so all the secrets are removed.
            self.secrets = None
            return self

        self.secrets = mask_sensitive_fields(cast(dict, self.secrets), secret_schema)
        return self


class ConnectionConfigurationResponseBase(ConnectionConfigSecretsMixin):
    """
    Base schema for ConnectionConfiguration responses,
    excluding fields that might be conditionally omitted.
    The mixin base class ensures that `secrets` sensitive values are masked.
    """

    name: Optional[str] = None
    key: FidesKey
    description: Optional[str] = None
    access: AccessLevel
    created_at: datetime
    updated_at: Optional[datetime] = None
    disabled: Optional[bool] = False
    last_test_timestamp: Optional[datetime] = None
    last_test_succeeded: Optional[bool] = None
    authorized: Optional[bool] = False
    enabled_actions: Optional[List[ActionType]] = None
    model_config = ConfigDict(from_attributes=True)


class ConnectionConfigurationResponseWithSystemKey(ConnectionConfigurationResponseBase):
    """
    Describes the full returned schema for a ConnectionConfiguration.
    """

    # Using this response with models returned from an async DB session will error
    # because the system_key is lazy loaded. Just a quirk of SQLAlchemy 1.4.
    system_key: Optional[str] = None


class ConnectionConfigurationResponse(ConnectionConfigurationResponseBase):
    """
    Describes the returned schema for a ConnectionConfiguration.
    """


class BulkPutConnectionConfiguration(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of ConnectionConfiguration responses."""

    succeeded: List[ConnectionConfigurationResponse]
    failed: List[BulkUpdateFailed]


class BulkPatchConnectionConfigurationWithSecrets(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of ConnectionConfigurationWithSecrets responses."""

    succeeded: List[ConnectionConfigurationResponse]
    failed: List[BulkUpdateFailed]


class SaasConnectionTemplateResponse(BaseModel):
    connection: ConnectionConfigurationResponse
    dataset: Dataset
