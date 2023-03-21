from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Union

from loguru import logger
from packaging.version import LegacyVersion, Version
from packaging.version import parse as parse_version
from sqlalchemy.orm import Session

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.schemas.connection_configuration.connection_config import (
    SaasConnectionTemplateValues,
)
from fides.api.ops.schemas.saas.connector_template import ConnectorTemplate
from fides.api.ops.schemas.saas.saas_config import SaaSConfig
from fides.api.ops.util.saas_util import (
    encode_file_contents,
    load_config,
    load_config_from_string,
    load_yaml_as_string,
    replace_config_placeholders,
    replace_dataset_placeholders,
)


class ConnectorTemplateLoader(ABC):
    @abstractmethod
    def get_connector_templates(self) -> Dict[str, ConnectorTemplate]:
        """Returns a map of connection templates"""


class FileConnectorTemplateLoader(ConnectorTemplateLoader):
    """
    Loads SaaS connector templates from the data/saas directory.
    """

    def __init__(self) -> None:
        self.templates: Dict[str, ConnectorTemplate] = {}
        for file in os.listdir("data/saas/config"):
            if file.endswith(".yml"):
                config_file = os.path.join("data/saas/config", file)
                config_dict = load_config(config_file)
                connector_type = config_dict["type"]
                human_readable = config_dict["name"]

                try:
                    icon = encode_file_contents(f"data/saas/icon/{connector_type}.svg")
                except FileNotFoundError:
                    logger.debug(
                        f"Could not find the expected {connector_type}.svg in the data/saas/icon/ directory, using default icon"
                    )
                    icon = encode_file_contents("data/saas/icon/default.svg")

                # store connector template for retrieval
                try:
                    self.templates[connector_type] = ConnectorTemplate(
                        config=load_yaml_as_string(config_file),
                        dataset=load_yaml_as_string(
                            f"data/saas/dataset/{connector_type}_dataset.yml"
                        ),
                        icon=icon,
                        human_readable=human_readable,
                    )
                except Exception:
                    logger.exception("Unable to load {} connector", connector_type)

    def get_connector_templates(self) -> Dict[str, ConnectorTemplate]:
        return self.templates


class ConnectorRegistry:

    _instance = None
    _templates: Dict[str, ConnectorTemplate] = {}

    @classmethod
    def get_instance(cls) -> "ConnectorRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._templates = (
                FileConnectorTemplateLoader().get_connector_templates()
            )
        return cls._instance

    @classmethod
    def connector_types(cls) -> List[str]:
        """List of registered SaaS connector types"""
        return list(cls.get_instance()._templates.keys())

    @classmethod
    def get_connector_template(cls, connector_type: str) -> Optional[ConnectorTemplate]:
        """
        Returns an object containing the various SaaS connector artifacts
        """
        return cls.get_instance()._templates.get(connector_type)


def create_connection_config_from_template_no_save(
    db: Session,
    template: ConnectorTemplate,
    template_values: SaasConnectionTemplateValues,
    system_id: Optional[str] = None,
) -> ConnectionConfig:
    """Creates a SaaS connection config from a template without saving it."""
    # Load saas config from template and replace every instance of "<instance_fides_key>" with the fides_key
    # the user has chosen
    config_from_template: Dict = replace_config_placeholders(
        template.config, "<instance_fides_key>", template_values.instance_key
    )

    data = {
        "name": template_values.name,
        "key": template_values.key,
        "description": template_values.description,
        "connection_type": ConnectionType.saas,
        "access": AccessLevel.write,
        "saas_config": config_from_template,
    }

    if system_id:
        data["system_id"] = system_id

    # Create SaaS ConnectionConfig
    connection_config = ConnectionConfig.create_without_saving(db, data=data)

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
    dataset_from_template: Dict = replace_dataset_placeholders(
        template.dataset, "<instance_fides_key>", template_values.instance_key
    )
    data = {
        "connection_config_id": connection_config.id,
        "fides_key": template_values.instance_key,
        "dataset": dataset_from_template,  # Currently used for upserting a CTL Dataset
    }
    dataset_config = DatasetConfig.upsert_with_ctl_dataset(db, data=data)
    return dataset_config


def update_saas_configs(db: Session) -> None:
    """
    Updates SaaS config instances currently in the DB if to the
    corresponding template in the registry are found.

    Effectively an "update script" for SaaS config instances,
    to be run on server bootstrap.
    """
    for connector_type in ConnectorRegistry.connector_types():
        logger.debug(
            "Determining if any updates are needed for connectors of type {} based on templates...",
            connector_type,
        )
        template: ConnectorTemplate = ConnectorRegistry.get_connector_template(  # type: ignore
            connector_type
        )
        saas_config = SaaSConfig(**load_config_from_string(template.config))
        template_version: Union[LegacyVersion, Version] = parse_version(
            saas_config.version
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
                    logger.exception(
                        "Encountered error attempting to update SaaS config instance {}",
                        saas_config_instance.fides_key,
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

    config_from_template: Dict = replace_config_placeholders(
        template.config, "<instance_fides_key>", template_vals.instance_key
    )

    connection_config.update_saas_config(db, SaaSConfig(**config_from_template))

    upsert_dataset_config_from_template(db, connection_config, template, template_vals)
