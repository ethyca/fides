from typing import Any, Dict, Generator

import pydash
import pytest
import requests
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from starlette.status import HTTP_204_NO_CONTENT

from fides.api.cryptography import cryptographic_util
from fides.api.db import session
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from tests.ops.test_helpers.db_utils import seed_postgres_data
from tests.ops.test_helpers.vault_client import get_secrets

secrets = get_secrets("twilio_conversations")


@pytest.fixture(scope="function")
def twilio_conversations_secrets(saas_config):
    return {
        "domain": pydash.get(saas_config, "twilio_conversations.domain")
        or secrets["domain"],
        "account_id": pydash.get(saas_config, "twilio_conversations.account_id")
        or secrets["account_id"],
        "password": pydash.get(saas_config, "twilio_conversations.password")
        or secrets["password"],
        "twilio_user_id": {
            "dataset": "twilio_postgres",
            "field": "twilio_users.twilio_user_id",
            "direction": "from",
        },
    }


@pytest.fixture(scope="function")
def twilio_conversations_identity_email(saas_config):
    return (
        pydash.get(saas_config, "twilio_conversations.identity_email")
        or secrets["identity_email"]
    )


@pytest.fixture(scope="session")
def twilio_conversations_erasure_identity_email():
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"


@pytest.fixture(scope="function")
def twilio_conversations_erasure_identity_name():
    return f"{cryptographic_util.generate_secure_random_string(13)}"


@pytest.fixture
def twilio_conversations_config() -> Dict[str, Any]:
    return load_config_with_replacement(
        "data/saas/config/twilio_conversations_config.yml",
        "<instance_fides_key>",
        "twilio_conversations_instance",
    )


@pytest.fixture
def twilio_conversations_dataset() -> Dict[str, Any]:
    return load_dataset_with_replacement(
        "data/saas/dataset/twilio_conversations_dataset.yml",
        "<instance_fides_key>",
        "twilio_conversations_instance",
    )[0]


@pytest.fixture(scope="function")
def twilio_conversations_connection_config(
    db: session, twilio_conversations_config, twilio_conversations_secrets
) -> Generator:
    fides_key = twilio_conversations_config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": twilio_conversations_secrets,
            "saas_config": twilio_conversations_config,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture
def twilio_conversations_dataset_config(
    db: Session,
    twilio_conversations_connection_config: ConnectionConfig,
    twilio_conversations_dataset: Dict[str, Any],
) -> Generator:
    fides_key = twilio_conversations_dataset["fides_key"]
    twilio_conversations_connection_config.name = fides_key
    twilio_conversations_connection_config.key = fides_key
    twilio_conversations_connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, twilio_conversations_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": twilio_conversations_connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    ctl_dataset.delete(db=db)


@pytest.fixture()
def twilio_postgres_dataset() -> Dict[str, Any]:
    return {
        "fides_key": "twilio_postgres",
        "name": "Twilio Postgres",
        "description": "Lookup for Twilio User IDs",
        "collections": [
            {
                "name": "twilio_users",
                "fields": [
                    {
                        "name": "email",
                        "data_categories": ["user.contact.email"],
                        "fidesops_meta": {"data_type": "string", "identity": "email"},
                    },
                    {
                        "name": "twilio_user_id",
                        "fidesops_meta": {"data_type": "string"},
                    },
                ],
            }
        ],
    }


@pytest.fixture
def twilio_postgres_dataset_config(
    connection_config: ConnectionConfig,
    twilio_postgres_dataset: Dict[str, Any],
    db: Session,
) -> Generator:
    fides_key = twilio_postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, twilio_postgres_dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset
    dataset.delete(db=db)
    dataset.delete(db=db)


@pytest.fixture(scope="function")
def twilio_postgres_db(postgres_integration_session):
    postgres_integration_session = seed_postgres_data(
        postgres_integration_session,
        "./tests/fixtures/saas/external_datasets/twilio.sql",
    )
    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def twilio_conversations_postgres_erasure_db(
    postgres_integration_session,
    twilio_conversations_erasure_identity_email,
    twilio_conversations_erasure_identity_name,
):
    if database_exists(postgres_integration_session.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(postgres_integration_session.bind.url)
    create_database(postgres_integration_session.bind.url)

    create_table_query = "CREATE TABLE public.twilio_users (email CHARACTER VARYING(100) PRIMARY KEY,twilio_user_id CHARACTER VARYING(100));"
    postgres_integration_session.execute(create_table_query)
    insert_query = (
        "INSERT INTO public.twilio_users VALUES('"
        + twilio_conversations_erasure_identity_email
        + "', '"
        + twilio_conversations_erasure_identity_name
        + "')"
    )
    postgres_integration_session.execute(insert_query)

    yield postgres_integration_session
    drop_database(postgres_integration_session.bind.url)


@pytest.fixture(scope="function")
def twilio_conversations_erasure_data(
    twilio_conversations_secrets,
    twilio_conversations_erasure_identity_name,
) -> Generator:
    """
    Creates a dynamic test data record for erasure tests.
    Yields user ID as this may be useful to have in test scenarios
    """

    base_url = f"https://{twilio_conversations_secrets['domain']}"
    auth = (
        twilio_conversations_secrets["account_id"],
        twilio_conversations_secrets["password"],
    )
    # Create user
    user_body = {
        "Identity": twilio_conversations_erasure_identity_name,
        "FriendlyName": "Test User",
    }
    users_response = requests.post(
        url=f"{base_url}/v1/Users", data=user_body, auth=auth
    )

    user = users_response.json()
    assert users_response.ok

    # Create conversation
    conversation_body = {"FriendlyName": "friendly_conversation"}
    conversations_response = requests.post(
        url=f"{base_url}/v1/Conversations", data=conversation_body, auth=auth
    )
    conversation = conversations_response.json()
    assert conversations_response.ok

    conversation_id = conversation["sid"]
    # Add conversation participant
    participant_body = {
        "FriendlyName": "friendly_conversation_participant",
        "Identity": twilio_conversations_erasure_identity_name,
    }
    participants_response = requests.post(
        url=f"{base_url}/v1/Conversations/" + conversation_id + "/Participants",
        data=participant_body,
        auth=auth,
    )
    participant = participants_response.json()

    assert conversations_response.ok

    # Add conversation message
    message_body = {
        "Author": twilio_conversations_erasure_identity_name,
        "Body": "Test Body",
    }
    messages_response = requests.post(
        url=f"{base_url}/v1/Conversations/" + conversation_id + "/Messages",
        data=message_body,
        auth=auth,
    )
    message = messages_response.json()

    assert messages_response.ok

    yield user, conversation, message, participant

    user_id = user["sid"]
    message_id = message["sid"]
    participant_id = participant["sid"]

    participant_delete_response = requests.delete(
        url=f"{base_url}/v1/Conversations/{conversation_id}/Participants/{participant_id}",
        auth=auth,
    )
    message_delete_response = requests.delete(
        url=f"{base_url}/v1/Conversations/{conversation_id}/Messages/{message_id}",
        auth=auth,
    )
    conversation_delete_response = requests.delete(
        url=f"{base_url}/v1/Conversations/" + conversation_id, auth=auth
    )
    user_delete_response = requests.delete(
        url=f"{base_url}/v1/Users/" + user_id, auth=auth
    )
    # we expect 204 if resource doesn't exist
    assert participant_delete_response.status_code == HTTP_204_NO_CONTENT
    assert message_delete_response.status_code == HTTP_204_NO_CONTENT
    assert conversation_delete_response.status_code == HTTP_204_NO_CONTENT
    assert user_delete_response.status_code == HTTP_204_NO_CONTENT
