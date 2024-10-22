from typing import Generator

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)


@pytest.fixture(scope="function")
def datahub_connection_config_no_secrets(
    db: Session,
) -> Generator[ConnectionConfig, None, None]:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": "DataHub Config",
            "key": "my_datahub_config",
            "connection_type": ConnectionType.datahub,
            "access": AccessLevel.write,
        },
    )
    yield connection_config
    connection_config.delete(db)
