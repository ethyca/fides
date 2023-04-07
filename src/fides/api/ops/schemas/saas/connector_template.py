from typing import Optional

from fideslang.models import Dataset
from pydantic import BaseModel, validator

from fides.api.ops.schemas.saas.saas_config import SaaSConfig
from fides.api.ops.util.saas_util import (
    load_config_from_string,
    load_dataset_from_string,
)


class ConnectorTemplate(BaseModel):
    """
    A collection of artifacts that make up a complete
    SaaS connector (SaaS config, dataset, icon, functions, etc.)
    """

    config: str
    dataset: str
    icon: Optional[str]
    functions: Optional[str]
    human_readable: str

    @validator("config")
    def validate_config(cls, config: str) -> str:
        """Validates the config at the given path"""
        saas_config = SaaSConfig(**load_config_from_string(config))
        if saas_config.fides_key != "<instance_fides_key>":
            raise ValueError(
                "Hard-coded fides_key detected in the config, replace all instances of it with <instance_fides_key>"
            )
        return config

    @validator("dataset")
    def validate_dataset(cls, dataset: str) -> str:
        """Validates the dataset at the given path"""
        saas_dataset = Dataset(**load_dataset_from_string(dataset))
        if saas_dataset.fides_key != "<instance_fides_key>":
            raise ValueError(
                "Hard-coded fides_key detected in the dataset, replace all instances of it with <instance_fides_key>"
            )
        return dataset
