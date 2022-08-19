import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Generator, List
from unittest import mock
from uuid import uuid4

import pydash
import pytest
import yaml
from faker import Faker
from fideslib.core.config import load_file, load_toml
from fideslib.models.audit_log import AuditLog, AuditLogAction
from fideslib.models.client import ClientDetail
from fideslib.models.fides_user import FidesUser
from fideslib.models.fides_user_permissions import FidesUserPermissions
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fidesops.ops.api.v1.scope_registry import PRIVACY_REQUEST_READ, SCOPE_REGISTRY
from fidesops.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fidesops.ops.models.datasetconfig import DatasetConfig
from fidesops.ops.models.email import EmailConfig
from fidesops.ops.models.policy import (
    ActionType,
    Policy,
    PolicyPostWebhook,
    PolicyPreWebhook,
    Rule,
    RuleTarget,
)
from fidesops.ops.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fidesops.ops.models.storage import ResponseFormat, StorageConfig
from fidesops.ops.schemas.email.email import (
    EmailServiceDetails,
    EmailServiceSecrets,
    EmailServiceSecretsMailgun,
    EmailServiceType,
)
from fidesops.ops.schemas.redis_cache import PrivacyRequestIdentity
from fidesops.ops.schemas.storage.storage import (
    FileNaming,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fidesops.ops.service.masking.strategy.masking_strategy_hmac import (
    HMAC_STRATEGY_NAME,
)
from fidesops.ops.service.masking.strategy.masking_strategy_nullify import (
    NULL_REWRITE_STRATEGY_NAME,
)
from fidesops.ops.service.masking.strategy.masking_strategy_string_rewrite import (
    STRING_REWRITE_STRATEGY_NAME,
)
from fidesops.ops.util.data_category import DataCategory

logging.getLogger("faker").setLevel(logging.ERROR)
# disable verbose faker logging
faker = Faker()
integration_config = load_toml(["fidesops-integration.toml"])

logger = logging.getLogger(__name__)


# Unified list of connections to integration dbs specified from fidesops-integration.toml

integration_secrets = {
    "postgres_example": {
        "host": pydash.get(integration_config, "postgres_example.server"),
        "port": pydash.get(integration_config, "postgres_example.port"),
        "dbname": pydash.get(integration_config, "postgres_example.db"),
        "username": pydash.get(integration_config, "postgres_example.user"),
        "password": pydash.get(integration_config, "postgres_example.password"),
    },
    "mongo_example": {
        "host": pydash.get(integration_config, "mongodb_example.server"),
        "defaultauthdb": pydash.get(integration_config, "mongodb_example.db"),
        "username": pydash.get(integration_config, "mongodb_example.user"),
        "password": pydash.get(integration_config, "mongodb_example.password"),
    },
    "mysql_example": {
        "host": pydash.get(integration_config, "mysql_example.server"),
        "port": pydash.get(integration_config, "mysql_example.port"),
        "dbname": pydash.get(integration_config, "mysql_example.db"),
        "username": pydash.get(integration_config, "mysql_example.user"),
        "password": pydash.get(integration_config, "mysql_example.password"),
    },
    "mssql_example": {
        "host": pydash.get(integration_config, "mssql_example.server"),
        "port": pydash.get(integration_config, "mssql_example.port"),
        "dbname": pydash.get(integration_config, "mssql_example.db"),
        "username": pydash.get(integration_config, "mssql_example.user"),
        "password": pydash.get(integration_config, "mssql_example.password"),
    },
    "mariadb_example": {
        "host": pydash.get(integration_config, "mariadb_example.server"),
        "port": pydash.get(integration_config, "mariadb_example.port"),
        "dbname": pydash.get(integration_config, "mariadb_example.db"),
        "username": pydash.get(integration_config, "mariadb_example.user"),
        "password": pydash.get(integration_config, "mariadb_example.password"),
    },
}


@pytest.fixture(scope="session", autouse=True)
def mock_upload_logic() -> Generator:
    with mock.patch(
        "fidesops.ops.service.storage.storage_uploader_service.upload_to_s3"
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
def email_config(db: Session) -> Generator:
    name = str(uuid4())
    email_config = EmailConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_email_config",
            "service_type": EmailServiceType.MAILGUN,
            "details": {
                EmailServiceDetails.API_VERSION.value: "v3",
                EmailServiceDetails.DOMAIN.value: "some.domain",
                EmailServiceDetails.IS_EU_DOMAIN.value: False,
            },
        },
    )
    email_config.set_secrets(
        db=db, email_secrets={EmailServiceSecrets.MAILGUN_API_KEY.value: "12984r70298r"}
    )
    yield email_config
    email_config.delete(db)


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
            "data_category": DataCategory("user.name").value,
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
            "data_category": DataCategory("user.name").value,
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
                "strategy": STRING_REWRITE_STRATEGY_NAME,
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
            "data_category": DataCategory("user.name").value,
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
            "masking_strategy": {
                "strategy": NULL_REWRITE_STRATEGY_NAME,
                "configuration": {},
            },
        },
    )

    # TODO set masking strategy in Rule.create() call above, once more masking strategies beyond NULL_REWRITE are supported.
    second_erasure_rule.masking_strategy = {
        "strategy": STRING_REWRITE_STRATEGY_NAME,
        "configuration": {"rewrite_value": "*****"},
    }

    second_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.email").value,
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
            "data_category": DataCategory("user").value,
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
def policy_drp_action(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    access_request_policy = Policy.create(
        db=db,
        data={
            "name": "example access request policy drp",
            "key": "example_access_request_policy_drp",
            "drp_action": "access",
            "client_id": oauth_client.id,
        },
    )

    access_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule DRP",
            "policy_id": access_request_policy.id,
            "storage_destination_id": storage_config.id,
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
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
def policy_drp_action_erasure(db: Session, oauth_client: ClientDetail) -> Generator:
    erasure_request_policy = Policy.create(
        db=db,
        data={
            "name": "example erasure request policy drp",
            "key": "example_erasure_request_policy_drp",
            "drp_action": "deletion",
            "client_id": oauth_client.id,
        },
    )

    erasure_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Request Rule DRP",
            "policy_id": erasure_request_policy.id,
            "masking_strategy": {
                "strategy": STRING_REWRITE_STRATEGY_NAME,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": erasure_request_rule.id,
        },
    )
    yield erasure_request_policy
    try:
        rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_request_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_request_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_policy_string_rewrite(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "string rewrite policy",
            "key": "string_rewrite_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "string rewrite erasure rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": STRING_REWRITE_STRATEGY_NAME,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    erasure_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        erasure_rule_target.delete(db)
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
def erasure_policy_hmac(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    erasure_policy = Policy.create(
        db=db,
        data={
            "name": "hmac policy",
            "key": "hmac_policy",
            "client_id": oauth_client.id,
        },
    )

    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "hmac erasure rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": HMAC_STRATEGY_NAME,
                "configuration": {},
            },
        },
    )

    erasure_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        erasure_rule_target.delete(db)
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


def _create_privacy_request_for_policy(
    db: Session,
    policy: Policy,
    status: PrivacyRequestStatus = PrivacyRequestStatus.in_processing,
) -> PrivacyRequest:
    data = {
        "external_id": f"ext-{str(uuid4())}",
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
        "status": status,
        "origin": f"https://example.com/",
        "policy_id": policy.id,
        "client_id": policy.client_id,
    }
    if status != PrivacyRequestStatus.pending:
        data["started_processing_at"] = datetime(
            2019,
            1,
            1,
            hour=1,
            minute=45,
            second=55,
            microsecond=393185,
            tzinfo=timezone.utc,
        )
    pr = PrivacyRequest.create(
        db=db,
        data=data,
    )
    pr.persist_identity(
        db=db,
        identity=PrivacyRequestIdentity(
            email="test@example.com",
            phone_number="+1 234 567 8910",
        ),
    )
    return pr


@pytest.fixture(scope="function")
def privacy_request(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def audit_log(db: Session, privacy_request) -> PrivacyRequest:
    audit_log = AuditLog.create(
        db=db,
        data={
            "user_id": "system",
            "privacy_request_id": privacy_request.id,
            "action": AuditLogAction.approved,
            "message": "",
        },
    )
    yield audit_log
    audit_log.delete(db)


@pytest.fixture(scope="function")
def privacy_request_status_pending(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
        PrivacyRequestStatus.pending,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_status_canceled(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
        PrivacyRequestStatus.canceled,
    )
    privacy_request.started_processing_at = None
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_drp_action(
    db: Session, policy_drp_action: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy_drp_action,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def succeeded_privacy_request(cache, db: Session, policy: Policy) -> PrivacyRequest:
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
    identity_kwargs = {"email": "email@example.com"}
    pr.cache_identity(identity_kwargs)
    pr.persist_identity(
        db=db,
        identity=PrivacyRequestIdentity(**identity_kwargs),
    )
    yield pr
    pr.delete(db)


@pytest.fixture(scope="function")
def user(db: Session):
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_fidesops_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=SCOPE_REGISTRY,
        user_id=user.id,
    )

    FidesUserPermissions.create(
        db=db, data={"user_id": user.id, "scopes": [PRIVACY_REQUEST_READ]}
    )

    db.add(client)
    db.commit()
    db.refresh(client)
    yield user
    try:
        client.delete(db)
    except ObjectDeletedError:
        pass
    user.delete(db)


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
def dataset_config(
    connection_config: ConnectionConfig,
    db: Session,
) -> Generator:
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
                                "data_categories": ["user.contact.email"],
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
    connection_config: ConnectionConfig, db: Session
) -> Generator:
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
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
                                "data_categories": ["user.contact.email"],
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
    yaml_file = load_file([filename])
    with open(yaml_file, "r") as file:
        return yaml.safe_load(file).get("dataset", [])


def load_dataset_as_string(filename: str) -> str:
    yaml_file = load_file([filename])
    with open(yaml_file, "r") as file:
        return file.read()


@pytest.fixture
def example_datasets() -> List[Dict]:
    example_datasets = []
    example_filenames = [
        "data/dataset/postgres_example_test_dataset.yml",
        "data/dataset/mongo_example_test_dataset.yml",
        "data/dataset/snowflake_example_test_dataset.yml",
        "data/dataset/redshift_example_test_dataset.yml",
        "data/dataset/mssql_example_test_dataset.yml",
        "data/dataset/mysql_example_test_dataset.yml",
        "data/dataset/mariadb_example_test_dataset.yml",
        "data/dataset/bigquery_example_test_dataset.yml",
        "data/dataset/manual_dataset.yml",
    ]
    for filename in example_filenames:
        example_datasets += load_dataset(filename)
    return example_datasets


@pytest.fixture
def example_yaml_datasets() -> str:
    example_filename = "data/dataset/example_test_datasets.yml"
    return load_dataset_as_string(example_filename)


@pytest.fixture
def example_yaml_dataset() -> str:
    example_filename = "data/dataset/postgres_example_test_dataset.yml"
    return load_dataset_as_string(example_filename)


@pytest.fixture
def example_invalid_yaml_dataset() -> str:
    example_filename = "data/dataset/example_test_dataset.invalid"
    return load_dataset_as_string(example_filename)


@pytest.fixture(scope="function")
def sample_data():
    return {
        "_id": 12345,
        "thread": [
            {
                "comment": "com_0001",
                "message": "hello, testing in-flight chat feature",
                "chat_name": "John",
                "messages": {},
            },
            {
                "comment": "com_0002",
                "message": "yep, got your message, looks like it works",
                "chat_name": "Jane",
            },
            {"comment": "com_0002", "message": "hello!", "chat_name": "Jeanne"},
        ],
        "snacks": ["pizza", "chips"],
        "seats": {"first_choice": "A2", "second_choice": "B3"},
        "upgrades": {
            "magazines": ["Time", "People"],
            "books": ["Once upon a Time", "SICP"],
            "earplugs": True,
        },
        "other_flights": [
            {"DFW": ["11 AM", "12 PM"], "CHO": ["12 PM", "1 PM"]},
            {"DFW": ["2 AM", "12 PM"], "CHO": ["2 PM", "1 PM"]},
            {"DFW": ["3 AM", "2 AM"], "CHO": ["2 PM", "1:30 PM"]},
        ],
        "months": {
            "july": [
                {
                    "activities": ["swimming", "hiking"],
                    "crops": ["watermelon", "cheese", "grapes"],
                },
                {"activities": ["tubing"], "crops": ["corn"]},
            ],
            "march": [
                {
                    "activities": ["skiing", "bobsledding"],
                    "crops": ["swiss chard", "swiss chard"],
                },
                {"activities": ["hiking"], "crops": ["spinach"]},
            ],
        },
        "hello": [1, 2, 3, 4, 2],
        "weights": [[1, 2], [3, 4]],
        "toppings": [[["pepperoni", "salami"], ["pepperoni", "cheese", "cheese"]]],
        "A": {"C": [{"M": ["p", "n", "n"]}]},
        "C": [["A", "B", "C", "B"], ["G", "H", "B", "B"]],  # Double lists
        "D": [
            [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
            [["A", "B", "C", "B"], ["G", "H", "B", "B"]],
        ],  # Triple lists
        "E": [[["B"], [["A", "B", "C", "B"], ["G", "H", "B", "B"]]]],  # Irregular lists
        "F": [
            "a",
            ["1", "a", [["z", "a", "a"]]],
        ],  # Lists elems are different types, not officially supported
    }


@pytest.fixture(scope="function")
def application_user(
    db,
    oauth_client,
) -> FidesUser:
    unique_username = f"user-{uuid4()}"
    user = FidesUser.create(
        db=db,
        data={
            "username": unique_username,
            "password": "test_password",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    oauth_client.user_id = user.id
    oauth_client.save(db=db)
    yield user
    user.delete(db=db)
