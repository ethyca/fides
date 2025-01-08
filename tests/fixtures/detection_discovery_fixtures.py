from typing import Generator

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.detection_discovery import MonitorConfig


@pytest.fixture(scope="function")
def monitor_config(
    db: Session, connection_config: ConnectionConfig
) -> Generator[MonitorConfig, None, None]:
    mc = MonitorConfig.create(
        db=db,
        data={
            "name": "test monitor config 1",
            "key": "test_monitor_config_1",
            "connection_config_id": connection_config.id,
            "classify_params": {
                "num_samples": 25,
                "num_threads": 2,
            },
            "databases": ["db1", "db2"],
            "execution_frequency": None,
            "execution_start_date": None,
        },
    )
    yield mc
    try:
        db.delete(mc)
    except ObjectDeletedError:
        # Object was already deleted, do nothing
        return


@pytest.fixture(scope="function")
def monitor_config_2(
    db: Session, connection_config: ConnectionConfig
) -> Generator[MonitorConfig, None, None]:
    mc = MonitorConfig.create(
        db=db,
        data={
            "name": "test monitor config 2",
            "key": "test_monitor_config_2",
            "connection_config_id": connection_config.id,
            "classify_params": {
                "num_samples": 20,
                "num_threads": 2,
            },
            "databases": ["db1", "db3"],
            "execution_frequency": None,
            "execution_start_date": None,
        },
    )
    yield mc
    try:
        db.delete(mc)
    except ObjectDeletedError:
        # Object was already deleted, do nothing
        return
