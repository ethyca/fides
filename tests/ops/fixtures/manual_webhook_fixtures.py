from uuid import uuid4

import pytest
from sqlalchemy.orm.exc import ObjectDeletedError

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.manual_webhook import AccessManualWebhook


@pytest.fixture(scope="function")
def integration_manual_webhook_config(db) -> ConnectionConfig:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "manual_webhook_example",
            "connection_type": ConnectionType.manual_webhook,
            "access": AccessLevel.read,
        },
    )
    yield connection_config
    try:
        connection_config.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def access_manual_webhook(db, integration_manual_webhook_config) -> ConnectionConfig:
    manual_webhook = AccessManualWebhook.create(
        db=db,
        data={
            "connection_config_id": integration_manual_webhook_config.id,
            "fields": [
                {"pii_field": "email", "dsr_package_label": "email"},
                {"pii_field": "Last Name", "dsr_package_label": "last_name"},
            ],
        },
    )
    yield manual_webhook
    try:
        manual_webhook.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def cached_input(privacy_request_requires_input, access_manual_webhook):
    privacy_request_requires_input.cache_manual_webhook_input(
        access_manual_webhook,
        {"email": "customer-1@example.com", "last_name": "McCustomer"},
    )
