from typing import Optional

from fideslang.validation import FidesKey
from pydantic import BaseModel

from fides.api.schemas.connection_configuration import connection_secrets_schemas


class SaasConnectionTemplateValues(BaseModel):
    """Schema with values to create both a Saas ConnectionConfig and DatasetConfig from a template"""

    name: Optional[str]  # For ConnectionConfig
    key: Optional[FidesKey]  # For ConnectionConfig
    description: Optional[str]  # For ConnectionConfig
    secrets: connection_secrets_schemas  # For ConnectionConfig
    instance_key: FidesKey  # For DatasetConfig.fides_key
