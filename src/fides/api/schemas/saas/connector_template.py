from typing import List, Optional

from fideslang.models import Dataset
from pydantic import BaseModel, field_validator

from fides.api.models.datasetconfig import validate_masking_strategy_override
from fides.api.schemas.enums.connection_category import ConnectionCategory
from fides.api.schemas.enums.integration_feature import IntegrationFeature
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.util.saas_util import load_config_from_string, load_dataset_from_string


class ConnectorTemplate(BaseModel):
    """
    A collection of artifacts that make up a complete
    SaaS connector (SaaS config, dataset, icon, etc.)
    """

    config: str
    dataset: str
    icon: Optional[str] = None
    human_readable: str
    authorization_required: bool
    user_guide: Optional[str] = None
    supported_actions: List[ActionType]
    category: Optional[ConnectionCategory] = None
    tags: Optional[List[str]] = None
    enabled_features: Optional[List[IntegrationFeature]] = None

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: str) -> str:
        """Validates the config at the given path"""
        saas_config = SaaSConfig(**load_config_from_string(value))
        if saas_config.fides_key != "<instance_fides_key>":
            raise ValueError(
                "Hard-coded fides_key detected in the config, replace all instances of it with <instance_fides_key>"
            )
        return value

    @field_validator("dataset")
    @classmethod
    def validate_dataset(cls, dataset: str) -> str:
        """Validates the dataset at the given path"""
        saas_dataset = Dataset(**load_dataset_from_string(dataset))
        validate_masking_strategy_override(saas_dataset)
        if saas_dataset.fides_key != "<instance_fides_key>":
            raise ValueError(
                "Hard-coded fides_key detected in the dataset, replace all instances of it with <instance_fides_key>"
            )
        return dataset
