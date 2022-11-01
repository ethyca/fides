from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Extra

from fides.api.ops.models.connectionconfig import AccessLevel, ConnectionType
from fides.api.ops.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.ops.schemas.connection_configuration import connection_secrets_schemas
from fides.api.ops.schemas.dataset import FidesopsDataset
from fides.api.ops.schemas.saas.saas_config import SaaSConfigBase
from fides.api.ops.schemas.shared_schemas import FidesOpsKey


class CreateConnectionConfiguration(BaseModel):
    """
    Schema for creating a ConnectionConfiguration

    Note that secrets are *NOT* allowed to be supplied here.
    """

    name: str
    key: Optional[FidesOpsKey]
    connection_type: ConnectionType
    access: AccessLevel
    disabled: Optional[bool] = False
    description: Optional[str]

    class Config:
        """Restrict adding other fields through this schema and set orm_mode to support mapping to ConnectionConfig"""

        orm_mode = True
        use_enum_values = True
        extra = Extra.forbid


class TestStatus(Enum):
    passed = "passed"
    failed = "failed"
    untested = "untested"

    def str_to_bool(self) -> Optional[bool]:
        """Translates query param string to optional/bool value
        for filtering ConnectionConfig.last_test_succeeded field"""
        if self == self.passed:
            return True
        if self == self.failed:
            return False
        return None


class SystemType(Enum):
    saas = "saas"
    database = "database"
    manual = "manual"


class ConnectionSystemTypeMap(BaseModel):
    """
    Describes the returned schema for connection types
    """

    identifier: Union[ConnectionType, str]
    type: SystemType
    human_readable: str
    encoded_icon: Optional[str]

    class Config:
        """Use enum values and set orm mode"""

        use_enum_values = True
        orm_mode = True


class ConnectionConfigurationResponse(BaseModel):
    """
    Describes the returned schema for a ConnectionConfiguration.

    Do *NOT* add "secrets" to this schema.
    """

    name: str
    key: FidesOpsKey
    description: Optional[str]
    connection_type: ConnectionType
    access: AccessLevel
    created_at: datetime
    updated_at: Optional[datetime]
    disabled: Optional[bool] = False
    last_test_timestamp: Optional[datetime]
    last_test_succeeded: Optional[bool]
    saas_config: Optional[SaaSConfigBase]

    class Config:
        """Set orm_mode to support mapping to ConnectionConfig"""

        orm_mode = True


class BulkPutConnectionConfiguration(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of ConnectionConfiguration responses."""

    succeeded: List[ConnectionConfigurationResponse]
    failed: List[BulkUpdateFailed]


class SaasConnectionTemplateValues(BaseModel):
    """Schema with values to create both a Saas ConnectionConfig and DatasetConfig from a template"""

    name: str  # For ConnectionConfig
    key: Optional[FidesOpsKey]  # For ConnectionConfig
    description: Optional[str]  # For ConnectionConfig
    secrets: connection_secrets_schemas  # For ConnectionConfig
    instance_key: FidesOpsKey  # For DatasetConfig.fides_key


class SaasConnectionTemplateResponse(BaseModel):
    connection: ConnectionConfigurationResponse
    dataset: FidesopsDataset
