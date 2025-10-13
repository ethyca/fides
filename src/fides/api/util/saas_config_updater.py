from typing import Iterable

from loguru import logger
from packaging.version import Version
from packaging.version import parse as parse_version
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
)
from fides.api.util.saas_util import load_config_from_string
from fides.service.connection.connection_service import ConnectionService
from fides.service.event_audit_service import EventAuditService


def update_saas_configs(db: Session) -> None:
    """
    Updates SaaS config instances currently in the DB if to the
    corresponding template in the registry are found.

    Effectively an "update script" for SaaS config instances,
    to be run on server bootstrap.
    """
    event_audit_service = EventAuditService(db)
    saas_connection_service = ConnectionService(db, event_audit_service)
    for connector_type in ConnectorRegistry.connector_types():
        logger.debug(
            "Determining if any updates are needed for connectors of type {} based on templates...",
            connector_type,
        )
        template: ConnectorTemplate = ConnectorRegistry.get_connector_template(  # type: ignore
            connector_type
        )
        saas_config = SaaSConfig(**load_config_from_string(template.config))
        template_version: Version = parse_version(saas_config.version)

        connection_configs: Iterable[ConnectionConfig] = ConnectionConfig.filter(
            db=db,
            conditions=(ConnectionConfig.saas_config["type"].astext == connector_type),
        ).all()
        for connection_config in connection_configs:
            saas_config_instance = SaaSConfig.model_validate(
                connection_config.saas_config
            )
            if parse_version(saas_config_instance.version) < template_version:
                logger.info(
                    "Updating SaaS config instance '{}' of type '{}' as its version, {}, was found to be lower than the template version {}",
                    saas_config_instance.fides_key,
                    connector_type,
                    saas_config_instance.version,
                    template_version,
                )
                try:
                    saas_connection_service.update_saas_instance(
                        connection_config,
                        template,
                        saas_config_instance,
                    )
                except Exception:
                    logger.exception(
                        "Encountered error attempting to update SaaS config instance {}",
                        saas_config_instance.fides_key,
                    )
