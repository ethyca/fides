from datetime import timezone
from datetime import datetime, timedelta
from typing import Dict, Generator, List
from unittest import mock
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError
import pytest
import yaml
import logging
from faker import Faker

from fidesops.core.config import load_file
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
)
from fidesops.models.privacy_request import (
    PrivacyRequest,
    PrivacyRequestStatus,
    ExecutionLog,
    ExecutionLogStatus,
)
from fidesops.models.storage import StorageConfig, ResponseFormat
from fidesops.schemas.storage.storage import (
    FileNaming,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fidesops.service.masking.strategy.masking_strategy_nullify import NULL_REWRITE
from fidesops.service.masking.strategy.masking_strategy_string_rewrite import STRING_REWRITE
from fidesops.service.privacy_request.request_runner_service import PrivacyRequestRunner
from fidesops.util.cache import FidesopsRedis

logging.getLogger("faker").setLevel(logging.ERROR)
# disable verbose faker logging
faker = Faker()


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
            "key": "my-test-config",
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
            "key": "my-onetrust-config",
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
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my-postgres-db-1",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "secrets": {
                "host": "postgres_example",
                "dbname": "postgres_example",
                "username": "postgres",
                "password": "postgres",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def read_connection_config(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my-postgres-db-1-read-config",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.read,
            "secrets": {
                "host": "postgres_example",
                "dbname": "postgres_example",
                "username": "postgres",
                "password": "postgres",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def connection_config_mysql(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my-mysql-db-1",
            "connection_type": ConnectionType.mysql,
            "access": AccessLevel.write,
            "secrets": {
                "host": "mysql_example",
                "dbname": "mysql_example",
                "username": "mysql_user",
                "password": "mysql_pw",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def connection_config_dry_run(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "postgres",
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
            "secrets": {
                "host": "postgres_example",
                "dbname": "postgres_example",
                "username": "postgres",
                "password": "postgres",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def mongo_connection_config(db: Session) -> Generator:
    name = str(uuid4())
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my-mongo-db-1",
            "connection_type": ConnectionType.mongodb,
            "access": AccessLevel.write,
            "secrets": {
                "host": "mongodb_example",
                "defaultauthdb": "mongo_test",
                "username": "mongo_user",
                "password": "mongo_pass",
            },
        },
    )
    yield connection_config
    connection_config.delete(db)


@pytest.fixture(scope="function")
def erasure_policy(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure policy",
            "key": "example-erasure-policy",
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
def erasure_policy_two_rules(db: Session, oauth_client: ClientDetail, erasure_policy: Policy) -> Generator:

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
        "configuration": {"rewrite_value": "*****"}
    }

    second_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.provided.identifiable.contact.email").value,
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
            "key": "example-access-request-policy",
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


@pytest.fixture
def example_datasets() -> List[Dict]:
    example_datasets = []
    example_filenames = [
        "data/dataset/postgres_example_test_dataset.yml",
        "data/dataset/mongo_example_test_dataset.yml",
    ]
    for filename in example_filenames:
        yaml_file = load_file(filename)
        with open(yaml_file, "r") as file:
            example_datasets += yaml.safe_load(file).get("dataset", [])
    return example_datasets


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
    db: Session,
    privacy_request: PrivacyRequest,
) -> Generator:
    yield PrivacyRequestRunner(
        cache=cache,
        db=db,
        privacy_request=privacy_request,
    )
