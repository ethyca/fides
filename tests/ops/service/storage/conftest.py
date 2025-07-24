from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.storage import ResponseFormat, StorageConfig
from fides.api.schemas.storage.storage import FileNaming, StorageDetails, StorageType


@pytest.fixture(scope="function")
def storage_config_local(db: Session) -> Generator:
    name = str(uuid4())
    data = {
        "name": name,
        "type": StorageType.local,
        "details": {
            StorageDetails.NAMING.value: FileNaming.request_id.value,
        },
        "key": "my_test_config_local",
        "format": ResponseFormat.json,
    }
    storage_config = StorageConfig.get_by_key_or_id(db, data=data)
    if storage_config is None:
        storage_config = StorageConfig.create(
            db=db,
            data=data,
        )
    yield storage_config
    storage_config.delete(db)
