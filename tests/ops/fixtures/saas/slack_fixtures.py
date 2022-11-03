from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from fideslib.db import session
from requests import Response
from sqlalchemy.orm import Session

from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("slack")


@pytest.fixture(scope="session")
def slack_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "slack.domain") or secrets["domain"],
        "access_token": pydash.get(saas_config, "slack.access_token")
        or secrets["access_token"],
    }


@pytest.fixture(scope="session")
def slack_identity_email(saas_config):
    return pydash.get(saas_config, "slack.identity_email") or secrets["identity_email"]


@pytest.fixture
def slack_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/slack_config.yml",
        "<instance_fides_key>",
        "slack_instance",
    )


@pytest.fixture
def slack_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/slack_dataset.yml",
        "<instance_fides_key>",
        "slack_instance",
    )[0]


@pytest.fixture(scope="function")
def slack_connection_config(db: session, slack_config, slack_secrets) -> Generator:
    fides_key = slack_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": slack_secrets,
            "saas_config": slack_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def slack_dataset_config(
    db: Session,
    slack_connection_config: ConnectionConfig,
    slack_dataset,
    slack_config,
) -> Generator:
    fides_key = slack_config["fides_key"]
    slack_connection_config.name = fides_key
    slack_connection_config.key = fides_key
    slack_connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": slack_connection_config.id,
            "fides_key": fides_key,
            "dataset": slack_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


class SlackTestClient:
    """Helper to call various Slack data management requests"""

    def __init__(self, slack_connection_config: ConnectionConfig):
        self.slack_secrets = slack_connection_config.secrets
        self.base_url = f"https://{self.slack_secrets['domain']}/api"
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {self.slack_secrets['access_token']}",
        }

    def get_user_from_email(self, email) -> Response:
        # get user id from email
        url = f"{self.base_url}/users.lookupByEmail?email={email}"
        user_response: Response = requests.get(url=url, headers=self.headers)
        return user_response


@pytest.fixture(scope="function")
def slack_test_client(
    slack_connection_config: SlackTestClient,
) -> Generator:
    test_client = SlackTestClient(slack_connection_config=slack_connection_config)
    yield test_client


@pytest.fixture(scope="function")
def slack_user_id(
    slack_test_client: SlackTestClient, slack_identity_email
) -> Generator:
    response = slack_test_client.get_user_from_email(email=slack_identity_email)
    if response.ok and response.json()["user"]:
        return response.json()["user"]["id"]
