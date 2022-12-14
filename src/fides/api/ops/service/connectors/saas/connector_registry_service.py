from __future__ import annotations

from os.path import exists
from typing import Dict, Iterable, List, Optional, Union

from loguru import logger
from packaging.version import LegacyVersion, Version
from packaging.version import parse as parse_version
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from toml import load as load_toml

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.schemas.connection_configuration.connection_config import (
    SaasConnectionTemplateValues,
)
from fides.api.ops.schemas.dataset import FidesopsDataset
from fides.api.ops.schemas.saas.saas_config import SaaSConfig
from fides.api.ops.util.saas_util import (
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
    human_readable: str

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


def upsert_dataset_config_from_template(
    db: Session,
    connection_config: ConnectionConfig,
    template: ConnectorTemplate,
    template_values: SaasConnectionTemplateValues,
) -> DatasetConfig:
    """
    Creates a `DatasetConfig` from a template
    and associates it with a ConnectionConfig.
    If the `DatasetConfig` already exists in the db,
    then the existing record is updated.
    """
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
    dataset_config = DatasetConfig.create_or_update(db, data=data)
    return dataset_config


def load_registry(config_file: str) -> ConnectorRegistry:
    """Loads a SaaS connector registry from the given config file."""
    global _registry  # pylint: disable=W0603
    if _registry is None:
        _registry = ConnectorRegistry.parse_obj(load_toml(config_file))
    return _registry


def update_saas_configs(registry: ConnectorRegistry, db: Session) -> None:
    """
    Updates SaaS config instances currently in the DB if to the
    corresponding template in the registry are found.

    Effectively an "update script" for SaaS config instances,
    to be run on server bootstrap.
    """
    for connector_type in registry.connector_types():
        logger.debug(
            "Determining if any updates are needed for connectors of type {} based on templates...",
            connector_type,
        )
        template: ConnectorTemplate = registry.get_connector_template(  # type: ignore
            connector_type
        )
        saas_config_template = SaaSConfig.parse_obj(load_config(template.config))
        template_version: Union[LegacyVersion, Version] = parse_version(
            saas_config_template.version
        )

        connection_configs: Iterable[ConnectionConfig] = ConnectionConfig.filter(
            db=db,
            conditions=(ConnectionConfig.saas_config["type"].astext == connector_type),
        ).all()
        for connection_config in connection_configs:
            saas_config_instance = SaaSConfig.parse_obj(connection_config.saas_config)
            if parse_version(saas_config_instance.version) < template_version:
                logger.info(
                    "Updating SaaS config instance '{}' of type '{}' as its version, {}, was found to be lower than the template version {}",
                    saas_config_instance.fides_key,
                    connector_type,
                    saas_config_instance.version,
                    template_version,
                )
                try:
                    update_saas_instance(
                        db,
                        connection_config,
                        template,
                        saas_config_instance,
                    )
                except Exception:
                    logger.error(
                        "Encountered error attempting to update SaaS config instance {}",
                        saas_config_instance.fides_key,
                        exc_info=True,
                    )


def update_saas_instance(
    db: Session,
    connection_config: ConnectionConfig,
    template: ConnectorTemplate,
    saas_config_instance: SaaSConfig,
) -> None:
    """
    Replace in the DB the existing SaaS instance configuration data
    (SaaSConfig, DatasetConfig) associated with the given ConnectionConfig
    with new instance configuration data based on the given ConnectorTemplate
    """
    template_vals = SaasConnectionTemplateValues(
        name=connection_config.name,
        key=connection_config.key,
        description=connection_config.description,
        secrets=connection_config.secrets,
        instance_key=saas_config_instance.fides_key,
    )

    config_from_template: Dict = load_config_with_replacement(
        template.config, "<instance_fides_key>", template_vals.instance_key
    )

    connection_config.update_saas_config(db, SaaSConfig(**config_from_template))

    upsert_dataset_config_from_template(db, connection_config, template, template_vals)
