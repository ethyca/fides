import os
from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.schemas.connection_configuration import OktaSchema

from .application_fixtures import integration_config


@pytest.fixture(scope="function")
def okta_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_okta_config",
            "connection_type": ConnectionType.okta,
            "access": AccessLevel.write,
        },
    )

    # Pulling from integration config file or GitHub secrets
    okta_integration_config = integration_config.get("okta", {})

    org_url = okta_integration_config.get("org_url") or os.environ.get("OKTA_ORG_URL")
    client_id = okta_integration_config.get("client_id") or os.environ.get(
        "OKTA_CLIENT_ID"
    )
    private_key = okta_integration_config.get("private_key") or os.environ.get(
        "OKTA_PRIVATE_KEY"
    )

    if not org_url:
        raise RuntimeError("Missing org_url for Okta")

    if not client_id:
        raise RuntimeError("Missing client_id for Okta")

    if not private_key:
        raise RuntimeError("Missing private_key for Okta")

    schema = OktaSchema(
        org_url=org_url,
        client_id=client_id,
        private_key=private_key,
    )
    connection_config.secrets = schema.model_dump()
    connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)
