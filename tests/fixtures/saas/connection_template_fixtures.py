from __future__ import annotations

from typing import Optional

import pytest

from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.schemas.connection_configuration.connection_config import (
    SaasConnectionTemplateValues,
)
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    ConnectorTemplate,
    create_connection_config_from_template_no_save,
    upsert_dataset_config_from_template,
)
from fides.api.ops.util.connection_util import validate_secrets


@pytest.fixture(scope="function")
def secondary_sendgrid_instance(db):
    """
    Instantiate a `sendgrid` SaaS connector instance
    Yields a tuple of the `ConnectionConfig` and `DatasetConfig`
    """
    secrets = {
        "domain": "test_sendgrid_domain",
        "api_key": "test_sendgrid_api_key",
    }
    connection_config, dataset_config = instantiate_connector(
        db,
        "sendgrid",
        "sendgrid_connection_config_secondary",
        "secondary_sendgrid_instance",
        "Sendgrid ConnectionConfig description",
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
        "mailchimp_connection_config_secondary",
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
        "mailchimp_connection_config_tertiary",
        "tertiary_mailchimp_instance",
    )
    yield connection_config, dataset_config
    dataset_config.delete(db)
    connection_config.delete(db)


def instantiate_mailchimp(db, key, fides_key) -> tuple[ConnectionConfig, DatasetConfig]:
    secrets = {
        "domain": "test_mailchimp_domain",
        "username": "test_mailchimp_username",
        "api_key": "test_mailchimp_api_key",
    }
    return instantiate_connector(
        db,
        "mailchimp",
        key,
        fides_key,
        "Mailchimp ConnectionConfig description",
        secrets,
    )


def instantiate_connector(
    db,
    connector_type,
    key,
    fides_key,
    description,
    secrets,
) -> tuple[ConnectionConfig, DatasetConfig]:
    """
    Helper to genericize instantiation of a SaaS connector
    """
    connector_template: Optional[
        ConnectorTemplate
    ] = ConnectorRegistry.get_connector_template(connector_type)
    template_vals = SaasConnectionTemplateValues(
        name=key,
        key=key,
        description=description,
        secrets=secrets,
        instance_key=fides_key,
    )

    connection_config = ConnectionConfig.filter(
        db=db, conditions=(ConnectionConfig.key == key)
    ).first()
    assert connection_config is None

    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(DatasetConfig.fides_key == fides_key),
    ).first()
    assert dataset_config is None

    connection_config: ConnectionConfig = (
        create_connection_config_from_template_no_save(
            db, connector_template, template_vals
        )
    )

    connection_config.secrets = validate_secrets(
        db, template_vals.secrets, connection_config
    ).dict()
    connection_config.save(db=db)  # Not persisted to db until secrets are validated

    dataset_config: DatasetConfig = upsert_dataset_config_from_template(
        db, connection_config, connector_template, template_vals
    )

    connection_config = ConnectionConfig.filter(
        db=db, conditions=(ConnectionConfig.key == key)
    ).first()
    assert connection_config is not None
    dataset_config = DatasetConfig.filter(
        db=db,
        conditions=(DatasetConfig.fides_key == fides_key),
    ).first()
    assert dataset_config is not None
    return connection_config, dataset_config
