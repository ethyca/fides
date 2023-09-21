import time
from typing import Optional

from fideslang.models import Dataset
from pydantic import BaseModel, validator

from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.service.authentication.authentication_strategy_oauth2_authorization_code import (
    OAuth2AuthorizationCodeAuthenticationStrategy,
)
from fides.api.util.saas_util import load_config_from_string, load_dataset_from_string


class ConnectorTemplate(BaseModel):
    """
    A collection of artifacts that make up a complete
    SaaS connector (SaaS config, dataset, icon, etc.)
    """

    config: str
    dataset: str
    icon: Optional[str]
    human_readable: str

    @validator("config")
    def validate_config(cls, config: str) -> str:
        """Validates the config at the given path"""
        start = time.monotonic()
        saas_config = SaaSConfig(**load_config_from_string(config))
        loaded_config = time.monotonic()
        if saas_config.fides_key != "<instance_fides_key>":
            raise ValueError(
                "Hard-coded fides_key detected in the config, replace all instances of it with <instance_fides_key>"
            )
        end = time.monotonic()
        print(f"took {loaded_config - start} to load config of {saas_config.name}")
        print(
            f"took {end - start} for full validate_config operation of {saas_config.name}"
        )
        return config

    @validator("dataset")
    def validate_dataset(cls, dataset: str) -> str:
        """Validates the dataset at the given path"""
        start = time.monotonic()
        saas_dataset = Dataset(**load_dataset_from_string(dataset))
        loaded_dataset = time.monotonic()
        if saas_dataset.fides_key != "<instance_fides_key>":
            raise ValueError(
                "Hard-coded fides_key detected in the dataset, replace all instances of it with <instance_fides_key>"
            )
        end = time.monotonic()
        print(f"took {loaded_dataset - start} to load dataset")
        print(f"took {end - start} for full validate_dataset operation")
        return dataset

    @property
    def authorization_required(self) -> bool:
        """Determines if the auth strategy for the given connector template requires authorization."""
        start = time.monotonic()
        config = SaaSConfig(**load_config_from_string(self.config))
        loaded_config = time.monotonic()
        authentication = config.client_config.authentication
        end = time.monotonic()
        print(f"took {loaded_config - start} to load config of {config.name}")
        print(
            f"took {end - start} for full authorization required operation of {config.name}"
        )
        return (
            authentication.strategy
            == OAuth2AuthorizationCodeAuthenticationStrategy.name
            if authentication
            else False
        )

    @property
    def user_guide(self) -> Optional[str]:
        start = time.monotonic()
        config = SaaSConfig(**load_config_from_string(self.config))
        end = time.monotonic()
        print(f"took {end - start} for full user_guide operation of {config.name}")
        return config.user_guide
