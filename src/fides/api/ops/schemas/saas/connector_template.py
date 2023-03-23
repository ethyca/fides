import yaml
from fideslang.models import Dataset
from pydantic import BaseModel, validator

from fides.api.ops.schemas.saas.saas_config import SaaSConfig


class ConnectorTemplate(BaseModel):
    """
    A collection of artifacts that make up a complete SaaS connector (SaaS config, dataset, etc.)
    """

    config: str
    dataset: str
    icon: str
    human_readable: str

    @validator("config")
    def validate_config(cls, config: str) -> str:
        """Validates the config at the given path"""
        SaaSConfig(**yaml.safe_load(config).get("saas_config"))
        return config

    @validator("dataset")
    def validate_dataset(cls, dataset: str) -> str:
        """Validates the dataset at the given path"""
        Dataset(**yaml.safe_load(dataset).get("dataset")[0])
        return dataset
