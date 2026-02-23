from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connection_oauth_credentials import OAuthConfig
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)


@pytest.fixture(scope="function")
def https_connection_config(db: Session) -> Generator[ConnectionConfig, None, None]:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_webhook_config",
            "connection_type": ConnectionType.https,
            "access": AccessLevel.read,
            "secrets": {
                "url": "http://example.com",
                "authorization": "test_authorization",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def https_connection_config_with_oauth(
    db: Session,
) -> Generator[ConnectionConfig, None, None]:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_webhook_oauth2_config",
            "connection_type": ConnectionType.https,
            "access": AccessLevel.read,
            "secrets": {
                "url": "https://example.com",
                "authorization": "test_authorization",
            },
        },
    )
    oauth2_config = OAuthConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "grant_type": "client_credentials",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "token_url": "https://example.com/token",
            "scope": "read write",
        },
    )

    yield connection_config
    connection_config.delete(db)
