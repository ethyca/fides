from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Self, cast

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

if TYPE_CHECKING:
    from fides.api.models.connectionconfig import ConnectionConfig


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

        t0 = time.perf_counter()
        connection_type = (
            self.saas_config.type
            if self.connection_type == ConnectionType.saas and self.saas_config
            else self.connection_type.value  # type: ignore
        )
        try:
            t_schema_start = time.perf_counter()
            secret_schema = get_connection_type_secret_schema(
                connection_type=connection_type
            )
            t_schema_ms = (time.perf_counter() - t_schema_start) * 1000
        except NoSuchConnectionTypeSecretSchemaError as e:
            logger.error(e)
            self.secrets = None
            return self

        t_mask_start = time.perf_counter()
        self.secrets = mask_sensitive_fields(cast(dict, self.secrets), secret_schema)
        t_mask_ms = (time.perf_counter() - t_mask_start) * 1000
        total_ms = (time.perf_counter() - t0) * 1000
        if total_ms > 10:
            logger.warning(
                "PERF mask_sensitive_values: conn_type={} total={:.1f}ms (schema_lookup={:.1f}ms, masking={:.1f}ms)",
                connection_type,
                total_ms,
                t_schema_ms,
                t_mask_ms,
            )
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


class LinkedSystemInfo(BaseModel):
    """Minimal system info embedded in connection config list responses."""

    fides_key: str
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ConnectionConfigurationResponse(ConnectionConfigurationResponseBase):
    """
    Describes the returned schema for a ConnectionConfiguration.
    """

    linked_systems: List[LinkedSystemInfo] = []

    @classmethod
    def from_connection_config(cls, config: ConnectionConfig) -> Self:
        """Build a response from an ORM ConnectionConfig, populating linked_systems."""
        response = cls.model_validate(config)
        if config.system:
            response.linked_systems = [
                LinkedSystemInfo(
                    fides_key=config.system.fides_key,
                    name=config.system.name,
                )
            ]
        return response


class ConnectionConfigurationResponseWithSystemKey(ConnectionConfigurationResponse):
    """Extended response that includes the legacy ``system_key`` field."""

    system_key: Optional[str] = None


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
