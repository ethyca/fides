from __future__ import annotations

from typing import Optional

import pytest

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    ConnectorTemplate,
)
from fides.api.util.connection_util import validate_secrets
from fides.service.connection.connection_service import ConnectionService
from fides.service.event_audit_service import EventAuditService


@pytest.fixture(scope="function")
def secondary_hubspot_instance(db):
    """
    Instantiate a `hubspot` SaaS connector instance
    Yields a tuple of the `ConnectionConfig` and `DatasetConfig`
    """
    secrets = {
        "domain": "test_hubspot_domain",
        "private_app_token": "test_hubspot_api_key",
    }
    audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, audit_service)
    connection_config, dataset_config = instantiate_connector(
        db,
        connection_service,
        "hubspot",
        "secondary_hubspot_instance",
        "Hubspot ConnectionConfig description",
        secrets,
    )
    yield connection_config, dataset_config
    dataset_config.delete(db)
    connection_config.delete(db)


@pytest.fixture(scope="function")
def secondary_mailchimp_instance(db):
    """
    Instantiate a `mailchimp` SaaS connector instance
    Yields a tuple of the `ConnectionConfig` and `DatasetConfig`
    """
    connection_config, dataset_config = instantiate_mailchimp(
        db,
        "secondary_mailchimp_instance",
    )
    yield connection_config, dataset_config
    dataset_config.delete(db)
    connection_config.delete(db)


@pytest.fixture(scope="function")
def tertiary_mailchimp_instance(db):
    """
    Instantiate a `mailchimp` SaaS connector instance
    Yields a tuple of the `ConnectionConfig` and `DatasetConfig`
    "Tertiary" is to distinguish this instance from the
    instance created by the `secondary_mailchimp_instance` fixture
    """
    connection_config, dataset_config = instantiate_mailchimp(
        db,
        "tertiary_mailchimp_instance",
    )
    yield connection_config, dataset_config
    dataset_config.delete(db)
    connection_config.delete(db)


def instantiate_mailchimp(db, fides_key) -> tuple[ConnectionConfig, DatasetConfig]:
    secrets = {
        "domain": "test_mailchimp_domain",
        "username": "test_mailchimp_username",
        "api_key": "test_mailchimp_api_key",
    }
    audit_service = EventAuditService(db)
    connection_service = ConnectionService(db, audit_service)
    return instantiate_connector(
        db,
        connection_service,
        "mailchimp",
        fides_key,
        "Mailchimp ConnectionConfig description",
        secrets,
    )


def instantiate_connector(
    db,
    connection_service: ConnectionService,
    connector_type,
    fides_key,
    description,
    secrets,
    system=None,
) -> tuple[ConnectionConfig, DatasetConfig]:
    """
    Helper to genericize instantiation of a SaaS connector
    """
    connector_template: Optional[ConnectorTemplate] = (
        ConnectorRegistry.get_connector_template(connector_type)
    )
    template_vals = SaasConnectionTemplateValues(
        key=fides_key,
        description=description,
        secrets=secrets,
        instance_key=fides_key,
    )

    connection_config = ConnectionConfig.filter(
        db=db, conditions=(ConnectionConfig.key == fides_key)
    ).first()
    assert connection_config is None

    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(DatasetConfig.fides_key == fides_key),
    ).first()
    assert dataset_config is None

    connection_config: ConnectionConfig = (
        connection_service.create_connection_config_from_template_no_save(
            connector_template, template_vals
        )
    )

    connection_config.secrets = validate_secrets(
        db, template_vals.secrets, connection_config
    ).model_dump(mode="json")
    connection_config.save(db=db)  # Not persisted to db until secrets are validated

    dataset_config: DatasetConfig = (
        connection_service.upsert_dataset_config_from_template(
            connection_config, connector_template, template_vals
        )
    )

    connection_config = ConnectionConfig.filter(
        db=db, conditions=(ConnectionConfig.key == fides_key)
    ).first()
    assert connection_config is not None
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(DatasetConfig.fides_key == fides_key),
    ).first()
    assert dataset_config is not None

    if system:
        system.connection_configs = connection_config
        db.commit()

    return connection_config, dataset_config
