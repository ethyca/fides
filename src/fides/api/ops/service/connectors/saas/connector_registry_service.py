from __future__ import annotations

from os.path import exists
from typing import Dict, List, Optional

from fideslib.core.config import load_toml
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.schemas.connection_configuration.connection_config import (
    SaasConnectionTemplateValues,
)
from fidesops.ops.schemas.dataset import FidesopsDataset
from fidesops.ops.schemas.saas.saas_config import SaaSConfig
from fidesops.ops.util.saas_util import (
    load_config,
    load_config_with_replacement,
    load_dataset,
    load_dataset_with_replacement,
)

_registry: Optional[ConnectorRegistry] = None
registry_file = "data/saas/saas_connector_registry.toml"


class ConnectorTemplate(BaseModel):
    """
    A collection of paths to artifacts that make up
    a complete SaaS connector (SaaS config, dataset, etc.)
    """

    config: str
    dataset: str
    icon: str

    @validator("config")
    def validate_config(cls, config: str) -> str:
        """Validates the config at the given path"""
        SaaSConfig(**load_config(config))
        return config

    @validator("dataset")
    def validate_dataset(cls, dataset: str) -> str:
        """Validates the dataset at the given path"""
        FidesopsDataset(**load_dataset(dataset)[0])
        return dataset

    @validator("icon")
    def validate_icon(cls, icon: str) -> str:
        """Validates the icon at the given path"""
        if not exists(icon):
            raise ValueError(f"Icon file {icon} was not found")
        return icon


class ConnectorRegistry(BaseModel):
    """A map of SaaS connector templates"""

    __root__: Dict[str, ConnectorTemplate]

    def connector_types(self) -> List[str]:
        """List of registered SaaS connector types"""
        return list(self.__root__)

    def get_connector_template(
        self, connector_type: str
    ) -> Optional[ConnectorTemplate]:
        """
        Returns an object containing the references to the various SaaS connector artifacts
        """
        return self.__root__.get(connector_type)


def create_connection_config_from_template_no_save(
    db: Session,
    template: ConnectorTemplate,
    template_values: SaasConnectionTemplateValues,
) -> ConnectionConfig:
    """Creates a SaaS connection config from a template without saving it."""
    # Load saas config from template and replace every instance of "<instance_fides_key>" with the fides_key
    # the user has chosen
    config_from_template: Dict = load_config_with_replacement(
        template.config, "<instance_fides_key>", template_values.instance_key
    )

    # Create SaaS ConnectionConfig
    connection_config = ConnectionConfig.create_without_saving(
        db,
        data={
            "name": template_values.name,
            "key": template_values.key,
            "description": template_values.description,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "saas_config": config_from_template,
        },
    )

    return connection_config


def create_dataset_config_from_template(
    db: Session,
    connection_config: ConnectionConfig,
    template: ConnectorTemplate,
    template_values: SaasConnectionTemplateValues,
) -> DatasetConfig:
    """Creates a DatasetConfig from a template and associates it with a ConnectionConfig"""
    # Load the dataset config from template and replace every instance of "<instance_fides_key>" with the fides_key
    # the user has chosen
    dataset_from_template: Dict = load_dataset_with_replacement(
        template.dataset, "<instance_fides_key>", template_values.instance_key
    )[0]
    data = {
        "connection_config_id": connection_config.id,
        "fides_key": template_values.instance_key,
        "dataset": dataset_from_template,
    }
    dataset_config = DatasetConfig.create(db, data=data)
    return dataset_config


def load_registry(config_file: str) -> ConnectorRegistry:
    """Loads a SaaS connector registry from the given config file."""
    global _registry  # pylint: disable=W0603
    if _registry is None:
        _registry = ConnectorRegistry.parse_obj(load_toml([config_file]))
    return _registry
