from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.db import session
from sqlalchemy.orm import Session

from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.saas_test_utils import poll_for_existence
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("datadog")


@pytest.fixture(scope="session")
def datadog_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "datadog.domain") or secrets["domain"],
        "api_key": pydash.get(saas_config, "datadog.api_key") or secrets["api_key"],
        "app_key": pydash.get(saas_config, "datadog.app_key") or secrets["app_key"],
    }


@pytest.fixture(scope="session")
def datadog_identity_email(saas_config):
    return (
        pydash.get(saas_config, "datadog.identity_email") or secrets["identity_email"]
    )


@pytest.fixture
def datadog_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/datadog_config.yml",
        "<instance_fides_key>",
        "datadog_instance",
    )


@pytest.fixture
def datadog_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/datadog_dataset.yml",
        "<instance_fides_key>",
        "datadog_instance",
    )[0]


@pytest.fixture(scope="function")
def datadog_connection_config(
    db: session, datadog_config, datadog_secrets
) -> Generator:
    fides_key = datadog_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": datadog_secrets,
            "saas_config": datadog_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def datadog_dataset_config(
    db: Session,
    datadog_connection_config: ConnectionConfig,
    datadog_dataset,
    datadog_config,
) -> Generator:
    fides_key = datadog_config["fides_key"]
    datadog_connection_config.name = fides_key
    datadog_connection_config.key = fides_key
    datadog_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": datadog_connection_config.id,
            "fides_key": fides_key,
            "dataset": datadog_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture(scope="session")
def datadog_access_data(datadog_secrets, datadog_identity_email):
    """
    Checks if logs exist for the identity email, logs are created if they
    don't exist and we poll until the logs are present in the events endpoint
    """

    if not _logs_exist(datadog_identity_email, datadog_secrets):
        url = "https://http-intake.logs.datadoghq.com/api/v2/logs"
        payload = [
            {
                "ddsource": "nginx",
                "ddtags": "env:staging,version:5.1",
                "hostname": "i-012345678",
                "message": f"2019-11-19T14:37:58,995 INFO [process.name][20081{i}] Hello {datadog_identity_email}",
                "service": "payment",
            }
            for i in range(25)
        ]
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "DD-API-KEY": datadog_secrets.get("api_key"),
        }
        requests.request("POST", url, headers=headers, json=payload)

        poll_for_existence(
            _logs_exist,
            (datadog_identity_email, datadog_secrets),
        )


def _logs_exist(datadog_identity_email: str, datadog_secrets):
    """Checks if logs exist for the given identity email"""

    url = "https://api.datadoghq.com/api/v2/logs/events"
    params = {
        "filter[from]": 0,
        "filter[query]": datadog_identity_email,
        "filter[to]": "now",
        "page[limit]": 1000,
    }
    headers = {
        "DD-API-KEY": datadog_secrets.get("api_key"),
        "DD-APPLICATION-KEY": datadog_secrets.get("app_key"),
    }
    response = requests.request("GET", url, params=params, headers=headers)

    if datadog_identity_email not in response.text:
        return None

    return response.json()
