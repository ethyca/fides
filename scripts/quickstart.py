"""
A five-step fidesops quickstart
"""
import json
import os
import time
from datetime import datetime
from os.path import exists
from time import sleep
from typing import Optional

import requests
import yaml
from loguru import logger

from fides.api.ops.api.v1 import urn_registry as ops_urls
from fides.api.ops.models.connectionconfig import ConnectionType
from fides.api.ops.models.policy import ActionType
from fides.core.config import get_config

CONFIG = get_config()


def get_access_token(client_id: str, client_secret: str) -> str:
    """
    Authorize with fidesops via OAuth.
    Returns a valid access token if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-OAuth-acquire_access_token_api_v1_oauth_token_post
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    url = f"{FIDESOPS_V1_API_URL}{ops_urls.TOKEN}"
    response = requests.post(url, data=data)

    if response.ok:
        token = (response.json())["access_token"]
        if token:
            logger.info(f"Completed fidesops oauth login via {url}")
            return token

    raise RuntimeError(
        f"fidesops oauth login failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_oauth_client():
    """
    Create a new OAuth client in fidesops.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-OAuth-acquire_access_token_api_v1_oauth_token_post
    See http://localhost:8000/api#operations-OAuth-acquire_access_token_api_v1_oauth_token_post
    """
    scopes_data = [
        "client:create",
        "client:update",
        "client:read",
        "client:delete",
        "policy:create_or_update",
        "policy:read",
        "policy:delete",
        "connection:create_or_update",
        "connection:read",
        "connection:delete",
        "privacy-request:read",
        "privacy-request:delete",
        "rule:create_or_update",
        "rule:read",
        "rule:delete",
        "storage:create_or_update",
        "storage:read",
        "storage:delete",
        "dataset:create_or_update",
        "dataset:read",
        "dataset:delete",
    ]
    url = f"{FIDESOPS_V1_API_URL}{ops_urls.CLIENT}"
    response = requests.post(
        url,
        headers=root_oauth_header,
        json=scopes_data,
    )

    if response.ok:
        created_client = response.json()
        if created_client["client_id"] and created_client["client_secret"]:
            logger.info(f"Created fidesops oauth client via {url}")
            return created_client

    raise RuntimeError(
        f"fidesops oauth client creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_connection(key: str, connection_type: ConnectionType):
    """
    Create a connection in fidesops for your PostgreSQL database
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Connections-put_connections_api_v1_connection_put
    """
    connection_create_data = [
        {
            "name": key,
            "key": key,
            "connection_type": connection_type.value,
            "access": "write",
        },
    ]
    url = f"{FIDESOPS_V1_API_URL}{ops_urls.CONNECTIONS}"
    response = requests.patch(
        url,
        headers=oauth_header,
        json=connection_create_data,
    )

    if response.ok:
        connections = (response.json())["succeeded"]
        if len(connections) > 0:
            logger.info(
                f"Created fidesops {connection_type.value} connection with key={key} via {url}"
            )
            return response.json()

    raise RuntimeError(
        f"fidesops connection creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def configure_postgres_connection(
    key: str, host: str, port: int, dbname: str, username: str, password: str
):
    """
    Configure the connection with the given `key` in fidesops with your PostgreSQL database credentials.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put
    """
    connection_secrets_data = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "username": username,
        "password": password,
    }
    connection_secrets_path = ops_urls.CONNECTION_SECRETS.format(connection_key=key)
    url = f"{FIDESOPS_V1_API_URL}{connection_secrets_path}"
    response = requests.put(
        url,
        headers=oauth_header,
        json=connection_secrets_data,
    )

    if response.ok:
        if (response.json())["test_status"] != "failed":
            logger.info(
                f"Configured fidesops postgres connection secrets for via {url}"
            )
            return response.json()

    raise RuntimeError(
        f"fidesops connection configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def configure_mongo_connection(
    key: str, host: str, port: int, dbname: str, username: str, password: str
):
    """
    Configure the connection with the given `key` in fidesops with your PostgreSQL database credentials.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Connections-put_connection_config_secrets_api_v1_connection__connection_key__secret_put
    """
    connection_secrets_data = {
        "host": host,
        "port": port,
        "defaultauthdb": dbname,
        "username": username,
        "password": password,
    }
    connection_secrets_path = ops_urls.CONNECTION_SECRETS.format(connection_key=key)
    url = f"{FIDESOPS_V1_API_URL}{connection_secrets_path}"
    response = requests.put(
        url,
        headers=oauth_header,
        json=connection_secrets_data,
    )

    if response.ok:
        if (response.json())["test_status"] != "failed":
            logger.info(f"Configured fidesops mongo connection secrets via {url}")
            return response.json()

    raise RuntimeError(
        f"fidesops connection configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def validate_dataset(connection_key: str, yaml_path: str):
    """
    Validate a dataset in fidesops given a YAML manifest file.
    Requires the `connection_key` for the connection, and `yaml_path`
    that is a local filepath to a .yml dataset Fides manifest file.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Datasets-validate_dataset_api_v1_connection__connection_key__validate_dataset_put
    """

    with open(yaml_path, "r") as file:
        dataset = yaml.safe_load(file).get("dataset", [])[0]

    validate_dataset_data = dataset
    dataset_validate_path = ops_urls.DATASET_VALIDATE.format(
        connection_key=connection_key
    )
    url = f"{FIDESOPS_V1_API_URL}{dataset_validate_path}"
    response = requests.put(
        url,
        headers=oauth_header,
        json=validate_dataset_data,
    )

    if response.ok:
        traversal_details = (response.json())["traversal_details"]
        if traversal_details["is_traversable"]:
            logger.info(f"Validated fidesops dataset via {url}")
            return response.json()
        else:
            raise RuntimeError(
                f"fidesops dataset is not traversable! traversal_details={traversal_details}"
            )
    print(vars(response))
    raise RuntimeError(
        f"fidesops dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_dataset(connection_key: str, yaml_path: str):
    """
    Create a dataset and a datasetconfig in fides given a YAML manifest file.
    Requires the `connection_key` for the PostgreSQL connection, and `yaml_path`
    that is a local filepath to a .yml dataset Fides manifest file.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Datasets-put_datasets_api_v1_connection__connection_key__dataset_put
    """

    with open(yaml_path, "r") as file:
        dataset = yaml.safe_load(file).get("dataset", [])[0]

    # Create ctl_dataset resource first
    dataset_create_data = [dataset]
    dataset_path = "/dataset/upsert"
    url = f"{FIDESOPS_V1_API_URL}{dataset_path}"
    response = requests.post(
        url,
        headers=oauth_header,
        json=dataset_create_data,
    )

    if response.ok:
        json_data = response.json()
        logger.info("{} via {}", json_data["message"], url)
    else:
        raise RuntimeError(
            f"fides dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    # Now link that ctl_dataset to the DatasetConfig
    dataset_config_path = ops_urls.DATASET_CONFIGS.format(connection_key=connection_key)
    url = f"{FIDESOPS_V1_API_URL}{dataset_config_path}"

    fides_key = dataset["fides_key"]
    response = requests.patch(
        url,
        headers=oauth_header,
        json=[{"fides_key": fides_key, "ctl_dataset_fides_key": fides_key}],
    )

    if response.ok:
        datasets = (response.json())["succeeded"]
        if len(datasets) > 0:
            logger.info(f"Created fidesops dataset config via {url}")
            return response.json()

    raise RuntimeError(
        f"fidesops dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_local_storage(key: str, file_format: str):
    """
    Create a storage config in fidesops to write to a local file.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Storage-put_config_api_v1_storage_config_put
    """
    storage_create_data = [
        {
            "name": key,
            "key": key,
            "type": "local",
            "download_format": file_format,
            "details": {
                "naming": "request_id",
            },
        },
    ]
    url = f"{FIDESOPS_V1_API_URL}{ops_urls.STORAGE_CONFIG}"
    response = requests.patch(
        url,
        headers=oauth_header,
        json=storage_create_data,
    )

    if response.ok:
        storage = (response.json())["succeeded"]
        if len(storage) > 0:
            logger.info(f"Created fidesops storage with key={key} via {url}")
            return response.json()

    raise RuntimeError(
        f"fidesops storage creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_dsr_policy(key: str):
    """
    Create a request policy in fidesops with the given key.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Policy-create_or_update_policies_api_v1_policy_put
    """

    policy_create_data = [
        {
            "name": key,
            "key": key,
        },
    ]
    url = f"{FIDESOPS_V1_API_URL}{ops_urls.POLICY_LIST}"
    response = requests.patch(
        url,
        headers=oauth_header,
        json=policy_create_data,
    )

    if response.ok:
        policies = (response.json())["succeeded"]
        if len(policies) > 0:
            logger.info("Created fidesops policy with key={} via {}", key, url)
            return response.json()

    raise RuntimeError(
        f"fidesops policy creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def delete_policy_rule(policy_key: str, key: str):
    """
    Deletes a policy rule with the given key.
    Returns the response JSON.
    See http://localhost:8000/api#operations-Policy-delete_rule_api_v1_policy__policy_key__rule__rule_key__delete
    """
    rule_path = ops_urls.RULE_DETAIL.format(policy_key=policy_key, rule_key=key)
    return requests.delete(f"{FIDESOPS_V1_API_URL}{rule_path}", headers=oauth_header)


def create_dsr_policy_rule(
    policy_key: str,
    key: str,
    action_type: ActionType,
    storage_destination_key: Optional[str] = None,
):
    """
    Create a policy rule to return matched data in an access request to the given storage destination.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Policy-create_or_update_rules_api_v1_policy__policy_key__rule_put
    """

    rule_create_data = {
        "name": key,
        "key": key,
        "action_type": action_type.value,
    }

    if action_type == ActionType.access:
        rule_create_data["storage_destination_key"] = storage_destination_key
    elif action_type == ActionType.erasure:
        # Only null masking supported currently
        rule_create_data["masking_strategy"] = {
            "strategy": "null_rewrite",
            "configuration": {},
        }

    rule_path = ops_urls.RULE_LIST.format(policy_key=policy_key)
    url = f"{FIDESOPS_V1_API_URL}{rule_path}"
    response = requests.patch(
        url,
        headers=oauth_header,
        json=[rule_create_data],
    )

    if response.ok:
        rules = (response.json())["succeeded"]
        if len(rules) > 0:
            logger.info(f"Created fidesops policy rule via {url}")
            return response.json()

    raise RuntimeError(
        f"fidesops policy rule creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_dsr_policy_rule_target(policy_key: str, rule_key: str, data_cat: str):
    """
    Create a policy rule target that matches the given data_category.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Policy-create_or_update_rule_targets_api_v1_policy__policy_key__rule__rule_key__target_put
    """

    target_create_data = [
        {
            "data_category": data_cat,
        },
    ]
    rule_target_path = ops_urls.RULE_TARGET_LIST.format(
        policy_key=policy_key, rule_key=rule_key
    )
    url = f"{FIDESOPS_V1_API_URL}{rule_target_path}"
    response = requests.patch(
        url,
        headers=oauth_header,
        json=target_create_data,
    )

    if response.ok:
        targets = (response.json())["succeeded"]
        if len(targets) > 0:
            logger.info(
                f"Created fidesops policy rule target for '{data_cat}' via {url}"
            )
            return response.json()

    raise RuntimeError(
        f"fidesops policy rule target creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_privacy_request(user_email: str, policy_key: str):
    """
    Create a privacy request that is executed against the given request policy.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-Privacy_Requests-create_privacy_request_api_v1_privacy_request_post
    """

    privacy_request_data = [
        {
            "requested_at": str(datetime.utcnow()),
            "policy_key": policy_key,
            "identity": {"email": user_email},
        },
    ]
    url = f"{FIDESOPS_V1_API_URL}{ops_urls.PRIVACY_REQUESTS}"
    response = requests.post(
        url,
        json=privacy_request_data,
    )

    if response.ok:
        created_privacy_requests = (response.json())["succeeded"]
        if len(created_privacy_requests) > 0:
            logger.info(f"Created fidesops privacy request for email={email} via {url}")
            return response.json()

    raise RuntimeError(
        f"fidesops privacy request creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def print_results(request_id: str) -> None:
    """
    Check to see if a result JSON for the given privacy request exists, and
    print it to the console if so.
    """
    results_path = f"fides_uploads/{request_id}.json"

    count = 0
    max_allowed_waiting = 10
    while not os.path.exists(results_path) and count < max_allowed_waiting:
        logger.info("Waiting for privacy request results...")
        time.sleep(5)
        count += 1  # Only loop through a reasonable number of times

    if exists(results_path):
        logger.info(
            f"Successfully read fidesops privacy request results from {results_path}:"
        )
        with open(results_path, "r") as file:
            results_json = json.loads(file.read())
            print(json.dumps(results_json, indent=4))
    else:
        raise RuntimeError(
            f"fidesops privacy request results not found at results_path={results_path}"
        )


if __name__ == "__main__":
    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        """
    ┌┬┐┬ ┬┌─┐  ┌─┐┬┌┬┐┌─┐┌─┐┌─┐┌─┐┌─┐  ┌─┐ ┬ ┬┬┌─┐┬┌─┌─┐┌┬┐┌─┐┬─┐┌┬┐
     │ ├─┤├┤   ├┤ │ ││├┤ └─┐│ │├─┘└─┐  │─┼┐│ │││  ├┴┐└─┐ │ ├─┤├┬┘ │
     ┴ ┴ ┴└─┘  └  ┴ ┴┘└─┘└─┘└─┘┴  └─┘  └─┘└└─┘┴└─┘┴ ┴└─┘ ┴ ┴ ┴┴└─ ┴
    """
    )

    # NOTE: In a real application, these secrets and config values would be provided
    # via ENV vars or similar, but we've inlined everything here for simplicity
    FIDESOPS_URL = "http://fides:8080"
    FIDESOPS_V1_API_URL = f"{FIDESOPS_URL}{ops_urls.V1_URL_PREFIX}"
    ROOT_CLIENT_ID = "fidesadmin"
    ROOT_CLIENT_SECRET = "fidesadminsecret"

    POSTGRES_SERVER = "host.docker.internal"
    POSTGRES_USER = "postgres"
    POSTGRES_PASSWORD = "postgres"
    POSTGRES_PORT = 6432
    POSTGRES_DB_NAME = "postgres_example"

    MONGO_SERVER = "mongodb_example"
    MONGO_USER = "mongo_user"
    MONGO_PASSWORD = "mongo_pass"
    MONGO_PORT = 27017
    MONGO_DB = "mongo_test"

    print(
        "-------------------------------------------------------------------------------------"
    )
    print("Setting up the fidesops environment with the following test configuration:")
    print(f"  FIDESOPS_URL = {FIDESOPS_URL}")
    print(f"  FIDESOPS_V1_API_URL = {FIDESOPS_V1_API_URL}")
    print(f"  ROOT_CLIENT_ID = {ROOT_CLIENT_ID}")
    print(f"  ROOT_CLIENT_SECRET = {ROOT_CLIENT_SECRET}")
    print(f"  POSTGRES_SERVER = {POSTGRES_SERVER}")
    print(f"  POSTGRES_USER = {POSTGRES_USER}")
    print(f"  POSTGRES_PASSWORD = {POSTGRES_PASSWORD}")
    print(f"  POSTGRES_PORT = {POSTGRES_PORT}")
    print(f"  POSTGRES_DB_NAME = {POSTGRES_DB_NAME}")
    print(f"  MONGO_SERVER = {MONGO_SERVER}")
    print(f"  MONGO_USER = {MONGO_USER}")
    print(f"  MONGO_PASSWORD = {MONGO_PASSWORD}")
    print(f"  MONGO_PORT = {MONGO_PORT}")
    print(f"  MONGO_DB = {MONGO_DB}")

    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        """
    ┌─┐┌┬┐┌─┐┌─┐  ┌─┐┌┐┌┌─┐
    └─┐ │ ├┤ ├─┘  │ ││││├┤     ...  Set up basic configuration
    └─┘ ┴ └─┘┴    └─┘┘└┘└─┘
    """
    )
    print(
        "-------------------------------------------------------------------------------------"
    )

    # Create a new OAuth client to use for your app
    print("Press [enter] to create an Oauth Token...")
    input()

    root_token = get_access_token(
        client_id=CONFIG.security.oauth_root_client_id,
        client_secret=CONFIG.security.oauth_root_client_secret,
    )
    root_oauth_header = {"Authorization": f"Bearer {root_token}"}
    client = create_oauth_client()
    access_token = get_access_token(
        client_id=client["client_id"], client_secret=client["client_secret"]
    )
    # In scope for all the methods below to use
    oauth_header = {"Authorization": f"Bearer {access_token}"}

    # Connect to your PostgreSQL database
    print(
        "-------------------------------------------------------------------------------------"
    )
    print("Press [enter] to connect fidesops to your test PostgreSQL database...")
    input()

    create_connection(
        key="test_application_postgres_db", connection_type=ConnectionType.postgres
    )
    configure_postgres_connection(
        key="test_application_postgres_db",
        host=POSTGRES_SERVER,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB_NAME,
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )

    # Connect to your Mongo database
    print(
        "-------------------------------------------------------------------------------------"
    )
    print("Press [enter] to connect fidesops to your test Mongo database...")
    input()

    create_connection(
        key="test_application_mongo_db", connection_type=ConnectionType.mongodb
    )
    sleep(5)
    configure_mongo_connection(
        key="test_application_mongo_db",
        host=MONGO_SERVER,
        port=MONGO_PORT,
        dbname=MONGO_DB,
        username=MONGO_USER,
        password=MONGO_PASSWORD,
    )

    # Upload the dataset YAML for your PostgreSQL schema
    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        "Press [enter] to define the data categories and relationships in your Postgres tables..."
    )
    input()

    validate_dataset(
        connection_key="test_application_postgres_db",
        yaml_path="data/dataset/postgres_example_test_dataset.yml",
    )
    postgres_dataset = create_dataset(
        connection_key="test_application_postgres_db",
        yaml_path="data/dataset/postgres_example_test_dataset.yml",
    )

    # Upload the dataset YAML for your MongoDB schema
    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        "Press [enter] to define the data categories and relationships in your Mongo collections..."
    )
    input()

    mongo_dataset = create_dataset(
        connection_key="test_application_mongo_db",
        yaml_path="data/dataset/mongo_example_test_dataset.yml",
    )

    # Configure a storage config to upload the results
    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        "Press [enter] to configure a storage destination to upload your final results (just local for now)..."
    )
    input()

    create_local_storage(
        key="example_storage",
        file_format="json",
    )

    # Create a policy that returns all user identifiable contact data
    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        """
    ┌─┐┌┬┐┌─┐┌─┐  ┌┬┐┬ ┬┌─┐
    └─┐ │ ├┤ ├─┘   │ ││││ │  ...  Create an access policy rule
    └─┘ ┴ └─┘┴     ┴ └┴┘└─┘
    """
    )
    print(
        "-------------------------------------------------------------------------------------"
    )
    data_category = "user"
    print(
        f"Press [enter] to create a Policy Rule that accesses information with the data category '{data_category}':"
    )
    input()

    create_dsr_policy(
        key="example_request_policy",
    )
    # Delete any existing policy rule so we can reconfigure it based on input
    delete_policy_rule(
        policy_key="example_request_policy",
        key="access_user_data",
    )
    create_dsr_policy_rule(
        policy_key="example_request_policy",
        key="access_user_data",
        action_type=ActionType.access,
        storage_destination_key="example_storage",
    )
    create_dsr_policy_rule_target(
        policy_key="example_request_policy",
        rule_key="access_user_data",
        data_cat=data_category,
    )

    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        """
    ┌─┐┌┬┐┌─┐┌─┐  ┌┬┐┬ ┬┬─┐┌─┐┌─┐
    └─┐ │ ├┤ ├─┘   │ ├─┤├┬┘├┤ ├┤    ...  Run an access privacy request
    └─┘ ┴ └─┘┴     ┴ ┴ ┴┴└─└─┘└─┘
    """
    )

    # Execute a privacy request
    print(
        "-------------------------------------------------------------------------------------"
    )
    email = "jane@example.com"
    print(
        f"Press [enter] to run an access request for {email} with Policy `example_request_policy`:"
    )
    input()
    print("Please wait...")
    privacy_requests = create_privacy_request(
        user_email=email,
        policy_key="example_request_policy",
    )
    privacy_request_id = privacy_requests["succeeded"][0]["id"]
    print_results(request_id=privacy_request_id)

    sleep(2)

    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        """
    ┌─┐┌┬┐┌─┐┌─┐  ┌─┐┌─┐┬ ┬┬─┐
    └─┐ │ ├┤ ├─┘  ├┤ │ ││ │├┬┘   ...  Create an erasure policy rule
    └─┘ ┴ └─┘┴    └  └─┘└─┘┴└─
    """
    )
    print(
        "-------------------------------------------------------------------------------------"
    )

    # Create a policy that erases all user data
    print(
        f"Press [enter] to create a Policy Rule describing how to erase information with the data category `{data_category}`:"
    )
    input()

    create_dsr_policy(
        key="example_erasure_policy",
    )
    # Delete any existing policy rule so we can reconfigure it based on input
    delete_policy_rule(
        policy_key="example_erasure_policy",
        key="erase_user_data",
    )
    create_dsr_policy_rule(
        policy_key="example_erasure_policy",
        key="erase_user_data",
        action_type=ActionType.erasure,
    )
    create_dsr_policy_rule_target(
        policy_key="example_erasure_policy",
        rule_key="erase_user_data",
        data_cat=data_category,
    )

    print(
        "-------------------------------------------------------------------------------------"
    )
    print(
        """
    ┌─┐┌┬┐┌─┐┌─┐  ┌─┐┬┬  ┬┌─┐
    └─┐ │ ├┤ ├─┘  ├┤ │└┐┌┘├┤     ...  Issue an erasure privacy request and verify
    └─┘ ┴ └─┘┴    └  ┴ └┘ └─┘
    """
    )
    print(
        "-------------------------------------------------------------------------------------"
    )

    # Execute a privacy request for jane@example.com
    email = "jane@example.com"
    print(
        f"Press [enter] to issue an erasure request for email {email}: with policy `example_erasure_policy`"
    )
    input()
    print("Please wait...")
    privacy_requests = create_privacy_request(
        user_email=email,
        policy_key="example_erasure_policy",
    )
    erasure_privacy_request_id = privacy_requests["succeeded"][0]["id"]

    print(
        f"Press [enter] to issue a follow-up access request to confirm removal of user data for {email}:"
    )
    input()
    print("Please wait...")
    privacy_requests = create_privacy_request(
        user_email=email,
        policy_key="example_request_policy",
    )
    print(
        "-------------------------------------------------------------------------------------"
    )
    access_result_id = privacy_requests["succeeded"][0]["id"]
    print_results(request_id=access_result_id)
    print(f"Jane's data has been removed for data category `{data_category}`.")
    exit(0)
