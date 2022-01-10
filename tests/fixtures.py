import logging
from datetime import datetime, timedelta, timezone
import os
from typing import Dict, Generator, List
from unittest import mock
from uuid import uuid4

import pydash
import pytest
import yaml
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fidesops.core.config import load_file, load_toml
from fidesops.models.client import ClientDetail
from fidesops.models.connectionconfig import (
    ConnectionConfig,
    AccessLevel,
    ConnectionType,
)
from fidesops.models.datasetconfig import DatasetConfig
from fidesops.models.policy import (
    ActionType,
    DataCategory,
    Policy,
    Rule,
    RuleTarget,
    PolicyPreWebhook,
    PolicyPostWebhook,
)
from fidesops.models.privacy_request import ExecutionLog
from fidesops.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    ExecutionLogStatus,
)
from fidesops.models.storage import StorageConfig, ResponseFormat
from fidesops.schemas.connection_configuration import (
    SnowflakeSchema,
    RedshiftSchema,
)
from fidesops.schemas.storage.storage import (
    FileNaming,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fidesops.service.masking.strategy.masking_strategy_nullify import NULL_REWRITE
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import (
    STRING_REWRITE,
)
from fidesops.service.privacy_request.request_runner_service import PrivacyRequestRunner
from fidesops.util.cache import FidesopsRedis

logging.getLogger("faker").setLevel(logging.ERROR)
# disable verbose faker logging
faker = Faker()
integration_config = load_toml("fidesops-integration.toml")


# Unified list of connections to integration dbs specified from fidesops-integration.toml

integration_secrets = {
    "postgres_example": {
        "host": pydash.get(integration_config, "postgres_example.SERVER"),
        "port": pydash.get(integration_config, "postgres_example.PORT"),
        "dbname": pydash.get(integration_config, "postgres_example.DB"),
        "username": pydash.get(integration_config, "postgres_example.USER"),
        "password": pydash.get(integration_config, "postgres_example.PASSWORD"),
    },
    "mongo_example": {
        "host": pydash.get(integration_config, "mongodb_example.SERVER"),
        "defaultauthdb": pydash.get(integration_config, "mongodb_example.DB"),
        "username": pydash.get(integration_config, "mongodb_example.USER"),
        "password": pydash.get(integration_config, "mongodb_example.PASSWORD"),
    },
    "mysql_example": {
        "host": pydash.get(integration_config, "mysql_example.SERVER"),
        "port": pydash.get(integration_config, "mysql_example.PORT"),
        "dbname": pydash.get(integration_config, "mysql_example.DB"),
        "username": pydash.get(integration_config, "mysql_example.USER"),
        "password": pydash.get(integration_config, "mysql_example.PASSWORD"),
    },
    "mssql_example": {
        "host": pydash.get(integration_config, "mssql_example.SERVER"),
        "port": pydash.get(integration_config, "mssql_example.PORT"),
        "dbname": pydash.get(integration_config, "mssql_example.DB"),
        "username": pydash.get(integration_config, "mssql_example.USER"),
        "password": pydash.get(integration_config, "mssql_example.PASSWORD"),
    },
}


@pytest.fixture(scope="session", autouse=True)
def mock_upload_logic() -> Generator:
    with mock.patch(
        "fidesops.service.storage.storage_uploader_service.upload_to_s3"
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="function")
def storage_config(db: Session) -> Generator:
    name = str(uuid4())
    storage_config = StorageConfig.create(
        db=db,
        data={
            "name": name,
            "type": StorageType.s3,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "key": "my_test_config",
            "format": ResponseFormat.json,
        },
    )
    storage_config.set_secrets(
        db=db,
        storage_secrets={
            StorageSecrets.AWS_ACCESS_KEY_ID.value: "1234",
            StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "5678",
        },
    )
    yield storage_config
    storage_config.delete(db)


@pytest.fixture(scope="function")
def storage_config_onetrust(db: Session) -> Generator:
    """
    This fixture adds onetrust config data to the database.
    """
    name = "onetrust config"
    storage_config = StorageConfig.create(
        db=db,
        data={
            "name": name,
            "type": StorageType.onetrust,
            "details": {
                StorageDetails.SERVICE_NAME.value: "Meow Services",
                StorageDetails.ONETRUST_POLLING_DAY_OF_WEEK.value: 1,
                StorageDetails.ONETRUST_POLLING_HR.value: 8,
            },
            "key": "my_onetrust_config",
        },
    )
    storage_config.set_secrets(
        db=db,
        storage_secrets={
            StorageSecrets.ONETRUST_CLIENT_SECRET.value: "23tcrcrewg",
            StorageSecrets.ONETRUST_CLIENT_ID.value: "9upqn3ufqnff",
            StorageSecrets.ONETRUST_HOSTNAME.value: "meow-services.onetrust",
        },
    )
    yield storage_config
    storage_config.delete(db)


@pytest.fixture(scope="function")
def connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_postgres_db_1",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "secrets": integration_secrets["postgres_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def read_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_postgres_db_1_read_config",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
            "secrets": integration_secrets["postgres_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def connection_config_mysql(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mysql_db_1",
            "connection_type": ConnectionType.mysql,
            "access": AccessLevel.write,
            "secrets": integration_secrets["mysql_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def connection_config_mssql(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mssql_db_1",
            "connection_type": ConnectionType.mssql,
            "access": AccessLevel.write,
            "secrets": integration_secrets["mssql_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def connection_config_dry_run(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "postgres",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "secrets": integration_secrets["postgres_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def mongo_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mongo_db_1",
            "connection_type": ConnectionType.mongodb,
            "access": AccessLevel.write,
            "secrets": integration_secrets["mongo_example"],
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def redshift_connection_config(db: Session) -> Generator:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_redshift_config",
            "connection_type": ConnectionType.redshift,
            "access": AccessLevel.write,
        },
    )
    uri = integration_config.get("redshift", {}).get("external_uri") or os.environ.get(
        "REDSHIFT_TEST_URI"
    )
    db_schema = integration_config.get("redshift", {}).get(
        "db_schema"
    ) or os.environ.get("REDSHIFT_TEST_DB_SCHEMA")
    if uri and db_schema:
        schema = RedshiftSchema(url=uri, db_schema=db_schema)
        connection_config.secrets = schema.dict()
        connection_config.save(db=db)

    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def snowflake_connection_config_without_secrets(
    db: Session,
) -> Generator:
    """
    Returns a Snowflake ConnectionConfig without secrets
    attached that is safe to usein any tests.
    """
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_snowflake_config",
            "connection_type": ConnectionType.snowflake,
            "access": AccessLevel.write,
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def snowflake_connection_config(
    db: Session,
    integration_config: Dict[str, str],
    snowflake_connection_config_without_secrets: ConnectionConfig,
) -> Generator:
    """
    Returns a Snowflake ConectionConfig with secrets attached if secrets are present
    in the configuration.
    """
    snowflake_connection_config = snowflake_connection_config_without_secrets
    uri = integration_config.get("snowflake", {}).get("external_uri") or os.environ.get(
        "SNOWFLAKE_TEST_URI"
    )
    if uri is not None:
        schema = SnowflakeSchema(url=uri)
        snowflake_connection_config.secrets = schema.dict()
        snowflake_connection_config.save(db=db)
    yield snowflake_connection_config


@pytest.fixture(scope="function")
def https_connection_config(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_webhook_config",
            "connection_type": ConnectionType.https,
            "access": AccessLevel.read,
            "secrets": {
                "url": "http://example.com",
                "authorization": "test_authorization",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def policy_pre_execution_webhooks(
    db: Session, https_connection_config, policy
) -> Generator:
    pre_webhook = PolicyPreWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "one_way",
            "name": str(uuid4()),
            "key": "pre_execution_one_way_webhook",
            "order": 0,
        },
    )
    pre_webhook_two = PolicyPreWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "two_way",
            "name": str(uuid4()),
            "key": "pre_execution_two_way_webhook",
            "order": 1,
        },
    )
    db.commit()
    yield [pre_webhook, pre_webhook_two]
    try:
        pre_webhook.delete(db)
    except ObjectDeletedError:
        pass
    try:
        pre_webhook_two.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def policy_post_execution_webhooks(
    db: Session, https_connection_config, policy
) -> Generator:
    post_webhook = PolicyPostWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "one_way",
            "name": str(uuid4()),
            "key": "cache_busting_webhook",
            "order": 0,
        },
    )
    post_webhook_two = PolicyPostWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "policy_id": policy.id,
            "direction": "one_way",
            "name": str(uuid4()),
            "key": "cleanup_webhook",
            "order": 1,
        },
    )
    db.commit()
    yield [post_webhook, post_webhook_two]
    try:
        post_webhook.delete(db)
    except ObjectDeletedError:
        pass
    try:
        post_webhook_two.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure policy",
            "key": "example_erasure_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": "null_rewrite",
                "configuration": {},
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.provided.identifiable.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_aes(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure policy aes",
            "key": "example_erasure_policy_aes",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": "aes_encrypt",
                "configuration": {},
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.provided.identifiable.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_string_rewrite_long(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure policy string rewrite",
            "key": "example_erasure_policy_string_rewrite",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": STRING_REWRITE,
                "configuration": {
                    "rewrite_value": "some rewrite value that is very long and goes on and on"
                },
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.provided.identifiable.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_two_rules(
    db: Session, oauth_client: ClientDetail, erasure_policy: Policy
) -> Generator:

    second_erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Second Erasure Rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {"strategy": NULL_REWRITE, "configuration": {}},
        },
    )

    # TODO set masking strategy in Rule.create() call above, once more masking strategies beyond NULL_REWRITE are supported.
    second_erasure_rule.masking_strategy = {
        "strategy": STRING_REWRITE,
        "configuration": {"rewrite_value": "*****"},
    }

    second_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory(
                "user.provided.identifiable.contact.email"
            ).value,
            "rule_id": second_erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        second_rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        second_erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def policy(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    access_request_policy = Policy.create(
        db=db,
        data={
            "name": "example access request policy",
            "key": "example_access_request_policy",
            "client_id": oauth_client.id,
        },
    )

    access_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule",
            "policy_id": access_request_policy.id,
            "storage_destination_id": storage_config.id,
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.provided.identifiable").value,
            "rule_id": access_request_rule.id,
        },
    )
    yield access_request_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_request_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_request_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def privacy_requests(db: Session, policy: Policy) -> Generator:
    privacy_requests = []
    for count in range(3):
        privacy_requests.append(
            PrivacyRequest.create(
                db=db,
                data={
                    "external_id": f"ext-{str(uuid4())}",
                    "started_processing_at": datetime.utcnow(),
                    "requested_at": datetime.utcnow() - timedelta(days=1),
                    "status": PrivacyRequestStatus.in_processing,
                    "origin": f"https://example.com/{count}/",
                    "policy_id": policy.id,
                    "client_id": policy.client_id,
                },
            )
        )
    yield privacy_requests
    for pr in privacy_requests:
        pr.delete(db)


@pytest.fixture(scope="function")
def privacy_request(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(
                2019,
                1,
                1,
                hour=1,
                minute=45,
                second=55,
                microsecond=393185,
                tzinfo=timezone.utc,
            ),
            "requested_at": datetime(
                2018,
                12,
                31,
                hour=2,
                minute=30,
                second=23,
                microsecond=916482,
                tzinfo=timezone.utc,
            ),
            "status": PrivacyRequestStatus.in_processing,
            "origin": f"https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def succeeded_privacy_request(db: Session, policy: Policy) -> PrivacyRequest:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 10, 1),
            "finished_processing_at": datetime(2021, 10, 3),
            "requested_at": datetime(2021, 10, 1),
            "status": PrivacyRequestStatus.complete,
            "origin": f"https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield pr
    pr.delete(db)


@pytest.fixture(scope="function")
def failed_privacy_request(db: Session, policy: Policy) -> PrivacyRequest:
    pr = PrivacyRequest.create(
        db=db,
        data={
            "external_id": f"ext-{str(uuid4())}",
            "started_processing_at": datetime(2021, 1, 1),
            "finished_processing_at": datetime(2021, 1, 2),
            "requested_at": datetime(2020, 12, 31),
            "status": PrivacyRequestStatus.error,
            "origin": f"https://example.com/",
            "policy_id": policy.id,
            "client_id": policy.client_id,
        },
    )
    yield pr
    pr.delete(db)


@pytest.fixture(scope="function")
def postgres_execution_log(
    db: Session, privacy_request: PrivacyRequest
) -> ExecutionLog:
    el = ExecutionLog.create(
        db=db,
        data={
            "dataset_name": "my-postgres-db",
            "collection_name": "user",
            "fields_affected": [
                {
                    "path": "my-postgres-db:user:email",
                    "field_name": "email",
                    "data_categories": ["user.provided.identifiable.contact.email"],
                }
            ],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.pending,
            "privacy_request_id": privacy_request.id,
        },
    )
    yield el
    el.delete(db)


@pytest.fixture(scope="function")
def second_postgres_execution_log(
    db: Session, privacy_request: PrivacyRequest
) -> ExecutionLog:
    el = ExecutionLog.create(
        db=db,
        data={
            "dataset_name": "my-postgres-db",
            "collection_name": "address",
            "fields_affected": [
                {
                    "path": "my-postgres-db:address:street",
                    "field_name": "street",
                    "data_categories": ["user.provided.identifiable.contact.street"],
                },
                {
                    "path": "my-postgres-db:address:city",
                    "field_name": "city",
                    "data_categories": ["user.provided.identifiable.contact.city"],
                },
            ],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.error,
            "privacy_request_id": privacy_request.id,
            "message": "Database timed out.",
        },
    )
    yield el
    el.delete(db)


@pytest.fixture(scope="function")
def mongo_execution_log(db: Session, privacy_request: PrivacyRequest) -> ExecutionLog:
    el = ExecutionLog.create(
        db=db,
        data={
            "dataset_name": "my-mongo-db",
            "collection_name": "orders",
            "fields_affected": [
                {
                    "path": "my-mongo-db:orders:name",
                    "field_name": "name",
                    "data_categories": ["user.provided.identifiable.contact.name"],
                }
            ],
            "action_type": ActionType.access,
            "status": ExecutionLogStatus.in_processing,
            "privacy_request_id": privacy_request.id,
        },
    )
    yield el
    el.delete(db)


@pytest.fixture(scope="function")
def dataset_config(connection_config: ConnectionConfig, db: Session) -> Generator:
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "postgres_example_subscriptions_dataset",
            "dataset": {
                "fides_key": "postgres_example_subscriptions_dataset",
                "name": "Postgres Example Subscribers Dataset",
                "description": "Example Postgres dataset created in test fixtures",
                "dataset_type": "PostgreSQL",
                "location": "postgres_example.test",
                "collections": [
                    {
                        "name": "subscriptions",
                        "fields": [
                            {
                                "name": "id",
                                "data_categories": ["system.operations"],
                            },
                            {
                                "name": "email",
                                "data_categories": [
                                    "user.provided.identifiable.contact.email"
                                ],
                                "fidesops_meta": {
                                    "identity": "email",
                                },
                            },
                        ],
                    },
                ],
            },
        },
    )
    yield dataset_config
    dataset_config.delete(db)


@pytest.fixture(scope="function")
def dataset_config_mysql(connection_config: ConnectionConfig, db: Session) -> Generator:
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "mysql_example_subscriptions_dataset",
            "dataset": {
                "fides_key": "mysql_example_subscriptions_dataset",
                "name": "Mysql Example Subscribers Dataset",
                "description": "Example Mysql dataset created in test fixtures",
                "dataset_type": "MySQL",
                "location": "mysql_example.test",
                "collections": [
                    {
                        "name": "subscriptions",
                        "fields": [
                            {
                                "name": "id",
                                "data_categories": ["system.operations"],
                            },
                            {
                                "name": "email",
                                "data_categories": [
                                    "user.provided.identifiable.contact.email"
                                ],
                                "fidesops_meta": {
                                    "identity": "email",
                                },
                            },
                        ],
                    },
                ],
            },
        },
    )
    yield dataset_config
    dataset_config.delete(db)


@pytest.fixture(scope="function")
def dataset_config_preview(
    connection_config_dry_run: ConnectionConfig, db: Session
) -> Generator:
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_dry_run.id,
            "fides_key": "postgres",
            "dataset": {
                "fides_key": "postgres",
                "name": "Postgres Example Subscribers Dataset",
                "description": "Example Postgres dataset created in test fixtures",
                "dataset_type": "PostgreSQL",
                "location": "postgres_example.test",
                "collections": [
                    {
                        "name": "subscriptions",
                        "fields": [
                            {
                                "name": "id",
                                "data_categories": ["system.operations"],
                            },
                            {
                                "name": "email",
                                "data_categories": [
                                    "user.provided.identifiable.contact.email"
                                ],
                                "fidesops_meta": {
                                    "identity": "email",
                                },
                            },
                        ],
                    },
                ],
            },
        },
    )
    yield dataset_config
    dataset_config.delete(db)


def load_dataset(filename: str) -> Dict:
    yaml_file = load_file(filename)
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file).get("dataset", [])


@pytest.fixture
def example_datasets() -> List[Dict]:
    example_datasets = []
    example_filenames = [
        "data/dataset/postgres_example_test_dataset.yml",
        "data/dataset/mongo_example_test_dataset.yml",
        "data/dataset/snowflake_example_test_dataset.yml",
        "data/dataset/redshift_example_test_dataset.yml",
    ]
    for filename in example_filenames:
        example_datasets += load_dataset(filename)
    return example_datasets


@pytest.fixture
def snowflake_example_test_dataset_config(
    snowflake_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    dataset = example_datasets[2]
    fides_key = dataset["fides_key"]
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": snowflake_connection_config.id,
            "fides_key": fides_key,
            "dataset": dataset,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)


@pytest.fixture
def redshift_example_test_dataset_config(
    redshift_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    dataset = example_datasets[3]
    fides_key = dataset["fides_key"]
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": redshift_connection_config.id,
            "fides_key": fides_key,
            "dataset": dataset,
        },
    )
    yield dataset_config
    dataset_config.delete(db=db)


@pytest.fixture
def postgres_example_test_dataset_config(
    connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0]
    fides_key = postgres_dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "dataset": postgres_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture
def postgres_example_test_dataset_config_read_access(
    read_connection_config: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    postgres_dataset = example_datasets[0]
    fides_key = postgres_dataset["fides_key"]
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": read_connection_config.id,
            "fides_key": fides_key,
            "dataset": postgres_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture
def mysql_example_test_dataset_config(
    connection_config_mysql: ConnectionConfig,
    db: Session,
    example_datasets: List[Dict],
) -> Generator:
    mysql_dataset = example_datasets[0]
    fides_key = mysql_dataset["fides_key"]
    connection_config_mysql.name = fides_key
    connection_config_mysql.key = fides_key
    connection_config_mysql.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config_mysql.id,
            "fides_key": fides_key,
            "dataset": mysql_dataset,
        },
    )
    yield dataset
    dataset.delete(db=db)


@pytest.fixture
def privacy_request_runner(
    cache: FidesopsRedis,
    privacy_request: PrivacyRequest,
) -> Generator:
    yield PrivacyRequestRunner(
        cache=cache,
        privacy_request=privacy_request,
    )
