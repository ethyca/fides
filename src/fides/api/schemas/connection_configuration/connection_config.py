from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from fideslang.models import Dataset
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import BaseModel, Extra, root_validator

from fides.api.common_exceptions import NoSuchConnectionTypeSecretSchemaError
from fides.api.models.connectionconfig import AccessLevel, ConnectionType
from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.connection_configuration import connection_secrets_schemas
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.saas_config import SaaSConfigBase
from fides.api.util.connection_type import get_connection_type_secret_schema


class CreateConnectionConfiguration(BaseModel):
    """
    Schema for creating a ConnectionConfiguration

    Note that secrets are *NOT* allowed to be supplied here.
    """

    name: Optional[str]
    key: Optional[FidesKey]
    connection_type: ConnectionType
    access: AccessLevel
    disabled: Optional[bool] = False
    description: Optional[str]
    enabled_actions: Optional[List[ActionType]] = None

    class Config:
        """Restrict adding other fields through this schema and set orm_mode to support mapping to ConnectionConfig"""

        orm_mode = True
        use_enum_values = True
        extra = Extra.forbid


class CreateConnectionConfigurationWithSecrets(CreateConnectionConfiguration):
    """Schema for creating a connection configuration including secrets."""

    secrets: Optional[connection_secrets_schemas] = None
    saas_connector_type: Optional[str]

    class Config:
        orm_mode = True
        extra = Extra.forbid


def mask_sensitive_fields(
    connection_secrets: Dict[str, Any], secret_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mask sensitive fields in the given secrets based on the provided schema.
    This function traverses the given secrets dictionary and uses the provided schema to
    identify fields that have been marked as sensitive. The function replaces the sensitive
    field values with a mask string ('********').
    Args:
        connection_secrets (Dict[str, Any]): The secrets to be masked.
        secret_schema (Dict[str, Any]): The schema defining which fields are sensitive.
    Returns:
        Dict[str, Any]: The secrets dictionary with sensitive fields masked.
    """
    if connection_secrets is None:
        return connection_secrets

    # The function `mask_sensitive_fields` is called recursively. The recursion can be stopped
    # if no properties are found at the current level, indicating that the current value is a dictionary.
    # Since individual fields within the dictionary do not need to be masked,
    # the function can return early in this case.
    if not secret_schema.get("properties"):
        return connection_secrets

    connection_secret_keys = connection_secrets.keys()
    secret_schema_keys = secret_schema["properties"].keys()
    new_connection_secrets = {}

    for key in connection_secret_keys:
        if key in secret_schema_keys:
            new_connection_secrets[key] = connection_secrets[key]

    for key, val in new_connection_secrets.items():
        prop = secret_schema["properties"].get(key, {})

        if isinstance(val, dict):
            mask_sensitive_fields(val, prop)
        elif prop.get("sensitive", False):
            new_connection_secrets[key] = "**********"

    return new_connection_secrets


class ConnectionConfigurationResponse(BaseModel):
    """
    Describes the returned schema for a ConnectionConfiguration.
    """

    name: Optional[str]
    key: FidesKey
    description: Optional[str]
    connection_type: ConnectionType
    access: AccessLevel
    created_at: datetime
    updated_at: Optional[datetime]
    disabled: Optional[bool] = False
    last_test_timestamp: Optional[datetime]
    last_test_succeeded: Optional[bool]
    saas_config: Optional[SaaSConfigBase]
    secrets: Optional[Dict[str, Any]]
    authorized: Optional[bool] = False

    @root_validator()
    def mask_sensitive_values(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive values in the response."""
        if values.get("secrets") is None:
            return values

        connection_type = (
            values["saas_config"].type
            if values.get("connection_type") == ConnectionType.saas
            else values.get("connection_type").value  # type: ignore
        )
        try:
            secret_schema = get_connection_type_secret_schema(
                connection_type=connection_type
            )
        except NoSuchConnectionTypeSecretSchemaError as e:
            logger.error(e)
            # if there is no schema, we don't know what values to mask.
            # so all the secrets are removed.
            values["secrets"] = None
            return values

        values["secrets"] = mask_sensitive_fields(
            cast(dict, values.get("secrets")), secret_schema
        )
        return values

    class Config:
        """Set orm_mode to support mapping to ConnectionConfig"""

        orm_mode = True


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
