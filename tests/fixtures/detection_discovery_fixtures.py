from typing import Generator

import pytest
from sqlalchemy.orm import Session

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
    db.delete(mc)


@pytest.fixture(scope="function")
def monitor_config_1_no_deletion(
    db: Session, connection_config: ConnectionConfig
) -> Generator[MonitorConfig, None, None]:
    """
    This fixture creates a monitor config that will NOT be cleaned up after the test,
    so the test itself should delete the monitor config. If your test does not delete
    the monitor config, use the `monitor_config` fixture instead.
    """
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


@pytest.fixture(scope="function")
def monitor_config_2_no_deletion(
    db: Session, connection_config: ConnectionConfig
) -> Generator[MonitorConfig, None, None]:
    """
    This fixture creates a monitor config that will NOT be cleaned up after the test,
    so the test itself should delete the monitor config. If your test does not delete
    the monitor config, use the `monitor_config` fixture instead.
    """
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
