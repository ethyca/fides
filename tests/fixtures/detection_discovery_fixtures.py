from typing import Generator

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.detection_discovery.core import MonitorConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.oauth.roles import VIEWER


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


@pytest.fixture(scope="function")
def monitor_steward(
    db: Session, monitor_config: MonitorConfig
) -> Generator[FidesUser, None, None]:
    """
    Create a user who is a steward of the monitor_config fixture.
    The user has VIEWER role and is assigned as a steward of the monitor.
    """
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_monitor_steward_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "monitor-steward.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[VIEWER],
        user_id=user.id,
        monitors=[monitor_config.id],
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [VIEWER]})

    db.add(client)
    db.commit()
    db.refresh(client)

    # Add user as steward of the monitor
    monitor_config.stewards.append(user)
    db.commit()
    db.refresh(monitor_config)

    yield user

    # Cleanup
    try:
        monitor_config.stewards.remove(user)
        db.commit()
    except (ValueError, ObjectDeletedError):
        pass
    user.delete(db)
