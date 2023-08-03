"""
Perform all setup and then run an Access + Erasure requests.

This script is intended to be run "locally" after spinning up
the required Docker containers.

Steps to run:
1. `nox -s dev -- postgres mongodb`
2. After everything is running, use another terminal windows: `python scripts/run_privacy_request.py`
"""
import json
import os
import time
from datetime import datetime
from os.path import exists
from time import sleep
from typing import Dict, Optional, Any

import requests
import yaml

from fides.api.models.connectionconfig import ConnectionType
from fides.api.schemas.policy import ActionType
from fides.common.api.scope_registry import SCOPE_REGISTRY
from fides.common.api.v1 import urn_registry as ops_urls
from fides.config import get_config

CONFIG = get_config()

# Defined as Global Constants for simplicity
FIDES_URL = os.getenv("FIDES__CLI__SERVER_HOST") or "localhost"
API_URL = f"http://{FIDES_URL}:8080{ops_urls.V1_URL_PREFIX}"
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


def perform_auth() -> Dict:
    """Perform Authorization Steps."""
    print("> Authorizing...")
    root_token = get_access_token(
        client_id=CONFIG.security.oauth_root_client_id,
        client_secret=CONFIG.security.oauth_root_client_secret,
    )
    root_header = {"Authorization": f"Bearer {root_token}"}
    client = create_oauth_client(root_header)
    access_token = get_access_token(
        client_id=client["client_id"], client_secret=client["client_secret"]
    )
    # In scope for all the methods below to use
    oauth_header = {"Authorization": f"Bearer {access_token}"}
    print("  - Authorization Complete!")
    return oauth_header


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
    url = f"{API_URL}{ops_urls.TOKEN}"
    response = requests.post(url, data=data)

    if response.ok:
        token = (response.json())["access_token"]
        if token:
            return token

    raise RuntimeError(
        f"fidesops oauth login failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_oauth_client(root_oauth_header: Dict) -> Dict:
    """
    Create a new OAuth client in fidesops.
    Returns the response JSON if successful, or throws an error otherwise.
    See http://localhost:8000/api#operations-OAuth-acquire_access_token_api_v1_oauth_token_post
    See http://localhost:8000/api#operations-OAuth-acquire_access_token_api_v1_oauth_token_post
    """
    url = f"{API_URL}{ops_urls.CLIENT}"
    response = requests.post(
        url,
        headers=root_oauth_header,
        json=SCOPE_REGISTRY,
    )

    if response.ok:
        created_client = response.json()
        if created_client["client_id"] and created_client["client_secret"]:
            return created_client

    raise RuntimeError(
        f"fidesops oauth client creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


# Do this up top so we can be lazy and use a global constant
OAUTH_HEADER = perform_auth()


def create_connection(key: str, connection_type: ConnectionType) -> Dict:
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
    url = f"{API_URL}{ops_urls.CONNECTIONS}"
    response = requests.patch(
        url,
        headers=OAUTH_HEADER,
        json=connection_create_data,
    )

    if response.ok:
        connections = (response.json())["succeeded"]
        if len(connections) > 0:
            return response.json()

    raise RuntimeError(
        f"fidesops connection creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def configure_postgres_connection(
    key: str, host: str, port: int, dbname: str, username: str, password: str
) -> Dict:
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
    url = f"{API_URL}{connection_secrets_path}"
    response = requests.put(
        url,
        headers=OAUTH_HEADER,
        json=connection_secrets_data,
    )

    if response.ok:
        if (response.json())["test_status"] != "failed":
            return response.json()

    raise RuntimeError(
        f"fidesops connection configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def configure_mongo_connection(
    key: str, host: str, port: int, dbname: str, username: str, password: str
) -> Dict:
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
    url = f"{API_URL}{connection_secrets_path}"
    response = requests.put(
        url,
        headers=OAUTH_HEADER,
        json=connection_secrets_data,
    )

    if response.ok:
        if (response.json())["test_status"] != "failed":
            return response.json()

    raise RuntimeError(
        f"fidesops connection configuration failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def validate_dataset(connection_key: str, yaml_path: str) -> Dict:
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
    url = f"{API_URL}{dataset_validate_path}"
    response = requests.put(
        url,
        headers=OAUTH_HEADER,
        json=validate_dataset_data,
    )

    if response.ok:
        traversal_details = (response.json())["traversal_details"]
        if traversal_details["is_traversable"]:
            return response.json()
        else:
            raise RuntimeError(
                f"fidesops dataset is not traversable! traversal_details={traversal_details}"
            )
    print(vars(response))
    raise RuntimeError(
        f"fidesops dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_dataset(connection_key: str, yaml_path: str) -> Dict:
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
    url = f"{API_URL}{dataset_path}"
    response = requests.post(
        url,
        headers=OAUTH_HEADER,
        json=dataset_create_data,
    )

    if response.ok:
        json_data = response.json()
    else:
        raise RuntimeError(
            f"fides dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
        )

    # Now link that ctl_dataset to the DatasetConfig
    dataset_config_path = ops_urls.DATASET_CONFIGS.format(connection_key=connection_key)
    url = f"{API_URL}{dataset_config_path}"

    fides_key = dataset["fides_key"]
    response = requests.patch(
        url,
        headers=OAUTH_HEADER,
        json=[{"fides_key": fides_key, "ctl_dataset_fides_key": fides_key}],
    )

    if response.ok:
        datasets = (response.json())["succeeded"]
        if len(datasets) > 0:
            return response.json()

    raise RuntimeError(
        f"fidesops dataset creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_local_storage(key: str, file_format: str) -> Dict:
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
            "format": file_format,
            "details": {
                "naming": "request_id",
            },
        },
    ]
    url = f"{API_URL}{ops_urls.STORAGE_CONFIG}"
    response = requests.patch(
        url,
        headers=OAUTH_HEADER,
        json=storage_create_data,
    )

    if response.ok:
        storage = (response.json())["succeeded"]
        if len(storage) > 0:
            return response.json()

    raise RuntimeError(
        f"fidesops storage creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_dsr_policy(key: str) -> Dict:
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
    url = f"{API_URL}{ops_urls.POLICY_LIST}"
    response = requests.patch(
        url,
        headers=OAUTH_HEADER,
        json=policy_create_data,
    )

    if response.ok:
        policies = (response.json())["succeeded"]
        if len(policies) > 0:
            return response.json()

    raise RuntimeError(
        f"fidesops policy creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def delete_policy_rule(policy_key: str, key: str) -> Any:
    """
    Deletes a policy rule with the given key.
    Returns the response JSON.
    See http://localhost:8000/api#operations-Policy-delete_rule_api_v1_policy__policy_key__rule__rule_key__delete
    """
    rule_path = ops_urls.RULE_DETAIL.format(policy_key=policy_key, rule_key=key)
    return requests.delete(f"{API_URL}{rule_path}", headers=OAUTH_HEADER)


def create_dsr_policy_rule(
    policy_key: str,
    key: str,
    action_type: ActionType,
    storage_destination_key: Optional[str] = None,
) -> Dict:
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
    url = f"{API_URL}{rule_path}"
    response = requests.patch(
        url,
        headers=OAUTH_HEADER,
        json=[rule_create_data],
    )

    if response.ok:
        rules = (response.json())["succeeded"]
        if len(rules) > 0:
            return response.json()

    raise RuntimeError(
        f"fidesops policy rule creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_dsr_policy_rule_target(
    policy_key: str, rule_key: str, data_cat: str
) -> Dict:
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
    url = f"{API_URL}{rule_target_path}"
    response = requests.patch(
        url,
        headers=OAUTH_HEADER,
        json=target_create_data,
    )

    if response.ok:
        targets = (response.json())["succeeded"]
        if len(targets) > 0:
            return response.json()

    raise RuntimeError(
        f"fidesops policy rule target creation failed! response.status_code={response.status_code}, response.json()={response.json()}"
    )


def create_privacy_request(
    policy_key: str, user_email: str = "jane@example.com"
) -> Dict:
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
    url = f"{API_URL}{ops_urls.PRIVACY_REQUESTS}"
    response = requests.post(
        url,
        json=privacy_request_data,
    )

    if response.ok:
        created_privacy_requests = (response.json())["succeeded"]
        if len(created_privacy_requests) > 0:
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
        time.sleep(5)
        count += 1  # Only loop through a reasonable number of times

    if exists(results_path):
        with open(results_path, "r") as file:
            results_json = json.loads(file.read())
            pretty_results = json.dumps(results_json, indent=4)
            print(f"> Erasure Results: {pretty_results}")
    else:
        raise RuntimeError(
            f"fidesops privacy request results not found at results_path={results_path}"
        )


def configure_datastores() -> None:
    """Configure the required datastores."""
    print("> Configuring Datastores...")

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
    print("  - Configured connection to Postgres.")

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
    print("  - Configured connection to Mongodb.")

    validate_dataset(
        connection_key="test_application_postgres_db",
        yaml_path="data/dataset/postgres_example_test_dataset.yml",
    )
    print("  - Validated dataset.")

    postgres_dataset = create_dataset(
        connection_key="test_application_postgres_db",
        yaml_path="data/dataset/postgres_example_test_dataset.yml",
    )
    print("  - Dataset uploaded to Postgres.")

    mongo_dataset = create_dataset(
        connection_key="test_application_mongo_db",
        yaml_path="data/dataset/mongo_example_test_dataset.yml",
    )
    print("  - Dataset uploaded to MongoDB.")

    create_local_storage(
        key="example_storage",
        file_format="json",
    )
    print("  - Created Local Storage.")


def configure_erasure_policies(data_category: str = "user") -> None:
    """Configure policies for erasure."""
    print("> Creating Erasure Policies...")
    create_dsr_policy(
        key="example_erasure_policy",
    )
    print("  - Erasure Policy Created.")

    # Remove any existing Policy Rules
    delete_policy_rule(
        policy_key="example_erasure_policy",
        key="erase_user_data",
    )
    create_dsr_policy_rule(
        policy_key="example_erasure_policy",
        key="erase_user_data",
        action_type=ActionType.erasure,
    )
    print("  - Policy Rule Created.")

    create_dsr_policy_rule_target(
        policy_key="example_erasure_policy",
        rule_key="erase_user_data",
        data_cat=data_category,
    )
    print("  - Policy Rule Target Created.")


def configure_access_policies(data_category: str = "user") -> None:
    """Configure policies for access."""
    print("> Creating Access Policies...")
    create_dsr_policy(
        key="example_request_policy",
    )
    print("  - Access Policy Created.")

    # Remove any existing Policy Rules
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
    print("  - Policy Rule Created.")

    create_dsr_policy_rule_target(
        policy_key="example_request_policy",
        rule_key="access_user_data",
        data_cat=data_category,
    )
    print("  - Policy Rule Target Created.")


def run_access_request(email: str = "jane@example.com") -> None:
    """Run an access request."""

    print(f"> Running Access request...")
    privacy_requests = create_privacy_request(
        user_email=email,
        policy_key="example_request_policy",
    )
    privacy_request_id = privacy_requests["succeeded"][0]["id"]
    print(f"  - Access request complete.")


def run_erasure_request(email: str = "jane@example.com") -> None:
    """Run an erasure request."""

    print(f"> Running Erasure request...")
    privacy_requests = create_privacy_request(
        user_email=email,
        policy_key="example_erasure_policy",
    )
    erasure_privacy_request_id = privacy_requests["succeeded"][0]["id"]
    print(f"  - Erasure request complete.")

    print("> Verifying Erasure Successful...")
    privacy_requests = create_privacy_request(
        user_email=email,
        policy_key="example_request_policy",
    )
    access_result_id = privacy_requests["succeeded"][0]["id"]
    print_results(request_id=access_result_id)


def run_privacy_request() -> None:
    """Perform the setup for a privacy request and run it."""

    configure_datastores()
    configure_access_policies()
    run_access_request()
    configure_erasure_policies()
    run_erasure_request()
    print("> Privacy Requests complete.")


if __name__ == "__main__":
    run_privacy_request()
