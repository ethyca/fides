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
    api_token = okta_integration_config.get("api_token") or os.environ.get(
        "OKTA_API_TOKEN"
    )

    if not org_url:
        raise RuntimeError("Missing org_url for Okta")

    if not api_token:
        raise RuntimeError("Missing api_token for Okta")

    schema = OktaSchema(
        org_url=org_url,
        api_token=api_token,
    )
    connection_config.secrets = schema.model_dump()
    connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)
