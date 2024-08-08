from typing import Any, Dict, Optional

from fideslang.validation import FidesKey
from pydantic import BaseModel, ConfigDict

from fides.api.models.connectionconfig import AccessLevel, ConnectionType
from fides.api.schemas.connection_configuration import connection_secrets_schemas


class SaasConnectionTemplateValues(BaseModel):
    """Schema with values to create both a Saas ConnectionConfig and DatasetConfig from a template"""

    name: Optional[str] = None  # For ConnectionConfig
    key: Optional[FidesKey] = None  # For ConnectionConfig
    description: Optional[str] = None  # For ConnectionConfig
    secrets: connection_secrets_schemas  # For ConnectionConfig
    instance_key: FidesKey  # For DatasetConfig.fides_key
    model_config = ConfigDict(extra="ignore")

    def generate_config_data_from_template(
        self, config_from_template: Dict
    ) -> Dict[str, Any]:
        """Generate a config data object (dict) based on the template values"""
        data = {
            "key": self.key if self.key else self.instance_key,
            "description": self.description,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,  # does this need to be passed as a method arg instead?
            "saas_config": config_from_template,
        }
        if self.name:
            data["name"] = self.name
        return data
