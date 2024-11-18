import logging
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Dict, Generator, List, Optional
from unittest import mock
from uuid import uuid4

import pydash
import pytest
import yaml
from faker import Faker
from fideslang.models import Dataset
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError, StaleDataError
from toml import load as load_toml

from fides.api.common_exceptions import SystemManagerException
from fides.api.graph.graph import DatasetGraph
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.audit_log import AuditLog, AuditLogAction
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig, convert_dataset_to_graph
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.location_regulation_selections import PrivacyNoticeRegion
from fides.api.models.messaging import MessagingConfig
from fides.api.models.messaging_template import MessagingTemplate
from fides.api.models.policy import (
    ActionType,
    Policy,
    PolicyPostWebhook,
    PolicyPreWebhook,
    Rule,
    RuleTarget,
)
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_experience import (
    PrivacyExperience,
    PrivacyExperienceConfig,
)
from fides.api.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNotice,
    PrivacyNoticeTemplate,
)
from fides.api.models.privacy_preference import (
    ConsentIdentitiesMixin,
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
    ServingComponent,
)
from fides.api.models.privacy_request import (
    Consent,
    ConsentRequest,
    PrivacyRequest,
    PrivacyRequestSource,
    PrivacyRequestStatus,
    ProvidedIdentity,
    RequestTask,
)
from fides.api.models.property import Property
from fides.api.models.registration import UserRegistration
from fides.api.models.sql_models import DataCategory as DataCategoryDbModel
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.models.sql_models import Organization, PrivacyDeclaration, System
from fides.api.models.storage import (
    ResponseFormat,
    StorageConfig,
    _create_local_default_storage,
    default_storage_config_name,
)
from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.oauth.roles import VIEWER
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceDetails,
    MessagingServiceSecrets,
    MessagingServiceType,
    MessagingTemplateWithPropertiesDetail,
)
from fides.api.schemas.property import Property as PropertySchema
from fides.api.schemas.property import PropertyType
from fides.api.schemas.redis_cache import (
    CustomPrivacyRequestField,
    Identity,
    LabeledIdentity,
)
from fides.api.schemas.storage.storage import (
    AWSAuthMethod,
    FileNaming,
    StorageDetails,
    StorageSecrets,
    StorageType,
)
from fides.api.service.connectors.fides.fides_client import FidesClient
from fides.api.service.masking.strategy.masking_strategy_hmac import HmacMaskingStrategy
from fides.api.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fides.api.service.masking.strategy.masking_strategy_random_string_rewrite import (
    RandomStringRewriteMaskingStrategy,
)
from fides.api.service.masking.strategy.masking_strategy_string_rewrite import (
    StringRewriteMaskingStrategy,
)
from fides.api.util.data_category import DataCategory, get_user_data_categories
from fides.config import CONFIG
from fides.config.helpers import load_file
from tests.ops.integration_tests.saas.connector_runner import (
    generate_random_email,
    generate_random_phone_number,
)

logging.getLogger("faker").setLevel(logging.ERROR)
# disable verbose faker logging
faker = Faker()
integration_config = load_toml("tests/ops/integration_test_config.toml")


# Unified list of connections to integration dbs specified from fides.api-integration.toml

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
    "google_cloud_sql_mysql_example": {
        "db_iam_user": pydash.get(
            integration_config, "google_cloud_sql_mysql_example.db_iam_user"
        ),
        "instance_connection_name": pydash.get(
            integration_config,
            "google_cloud_sql_mysql_example.instance_connection_name",
        ),
        "dbname": pydash.get(
            integration_config, "google_cloud_sql_mysql_example.dbname"
        ),
        "keyfile_creds": pydash.get(
            integration_config, "google_cloud_sql_mysql_example.keyfile_creds"
        ),
    },
    "google_cloud_sql_postgres_example": {
        "db_iam_user": pydash.get(
            integration_config, "google_cloud_sql_postgres_example.db_iam_user"
        ),
        "instance_connection_name": pydash.get(
            integration_config,
            "google_cloud_sql_postgres_example.instance_connection_name",
        ),
        "dbname": pydash.get(
            integration_config, "google_cloud_sql_postgres_example.dbname"
        ),
        "keyfile_creds": pydash.get(
            integration_config, "google_cloud_sql_postgres_example.keyfile_creds"
        ),
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
    "timescale_example": {
        "host": pydash.get(integration_config, "timescale_example.server"),
        "port": pydash.get(integration_config, "timescale_example.port"),
        "dbname": pydash.get(integration_config, "timescale_example.db"),
        "username": pydash.get(integration_config, "timescale_example.user"),
        "password": pydash.get(integration_config, "timescale_example.password"),
    },
    "fides_example": {
        "uri": pydash.get(integration_config, "fides_example.uri"),
        "username": pydash.get(integration_config, "fides_example.username"),
        "password": pydash.get(integration_config, "fides_example.password"),
        "polling_timeout": pydash.get(
            integration_config, "fides_example.polling_timeout"
        ),
    },
    "dynamodb_example": {
        "region": pydash.get(integration_config, "dynamodb_example.region"),
        "aws_access_key_id": pydash.get(
            integration_config, "dynamodb_example.aws_access_key_id"
        ),
        "aws_secret_access_key": pydash.get(
            integration_config, "dynamodb_example.aws_secret_access_key"
        ),
    },
    "scylla_example": {
        "host": pydash.get(integration_config, "scylladb_example.server"),
        "username": pydash.get(integration_config, "scylladb_example.username"),
        "password": pydash.get(integration_config, "scylladb_example.password"),
    },
    "rds_mysql_example": {
        "aws_access_key_id": pydash.get(
            integration_config, "rds_mysql_example.aws_access_key_id"
        ),
        "aws_secret_access_key": pydash.get(
            integration_config,
            "rds_mysql_example.aws_secret_access_key",
        ),
        "db_username": pydash.get(integration_config, "rds_mysql_example.db_username"),
        "db_instance": pydash.get(integration_config, "rds_mysql_example.db_instance"),
        "db_name": pydash.get(integration_config, "rds_mysql_example.db_name"),
        "region": pydash.get(integration_config, "rds_mysql_example.region"),
    },
    "rds_postgres_example": {
        "aws_access_key_id": pydash.get(
            integration_config, "rds_postgres_example.aws_access_key_id"
        ),
        "aws_secret_access_key": pydash.get(
            integration_config,
            "rds_postgres_example.aws_secret_access_key",
        ),
        "db_username": pydash.get(
            integration_config, "rds_postgres_example.db_username"
        ),
        "db_instance": pydash.get(
            integration_config, "rds_postgres_example.db_instance"
        ),
        "db_name": pydash.get(integration_config, "rds_postgres_example.db_name"),
        "region": pydash.get(integration_config, "rds_postgres_example.region"),
    },
}


@pytest.fixture(scope="session", autouse=True)
def mock_upload_logic() -> Generator:
    with mock.patch(
        "fides.api.service.storage.storage_uploader_service.upload_to_s3"
    ) as _fixture:
        _fixture.return_value = "http://www.data-download-url"
        yield _fixture


@pytest.fixture(scope="function")
def custom_data_category(db: Session) -> Generator:
    category = DataCategoryDbModel.create(
        db=db,
        data={
            "name": "Example Custom Data Category",
            "description": "A custom data category for testing",
            "fides_key": "test_custom_data_category",
        },
    )
    yield category
    category.delete(db)


@pytest.fixture(scope="function")
def storage_config(db: Session) -> Generator:
    name = str(uuid4())
    storage_config = StorageConfig.create(
        db=db,
        data={
            "name": name,
            "type": StorageType.s3,
            "details": {
                StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
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
def storage_config_local(db: Session) -> Generator:
    name = str(uuid4())
    storage_config = StorageConfig.create(
        db=db,
        data={
            "name": name,
            "type": StorageType.local,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
            },
            "key": "my_test_config_local",
            "format": ResponseFormat.json,
        },
    )
    yield storage_config
    storage_config.delete(db)


@pytest.fixture(scope="function")
def storage_config_default(db: Session) -> Generator:
    """
    Create and yield a default storage config, as defined by its
    `is_default` flag being set to `True`. This is an s3 storage config.
    """
    sc = StorageConfig.create(
        db=db,
        data={
            "name": default_storage_config_name(StorageType.s3.value),
            "type": StorageType.s3,
            "is_default": True,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
                StorageDetails.AUTH_METHOD.value: AWSAuthMethod.AUTOMATIC.value,
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "format": ResponseFormat.json,
        },
    )
    yield sc


@pytest.fixture(scope="function")
def storage_config_default_s3_secret_keys(db: Session) -> Generator:
    """
    Create and yield a default storage config, as defined by its
    `is_default` flag being set to `True`. This is an s3 storage config.
    """
    sc = StorageConfig.create(
        db=db,
        data={
            "name": default_storage_config_name(StorageType.s3.value),
            "type": StorageType.s3,
            "is_default": True,
            "details": {
                StorageDetails.NAMING.value: FileNaming.request_id.value,
                StorageDetails.AUTH_METHOD.value: AWSAuthMethod.SECRET_KEYS.value,
                StorageDetails.BUCKET.value: "test_bucket",
            },
            "secrets": {
                StorageSecrets.AWS_ACCESS_KEY_ID.value: "access_key_id",
                StorageSecrets.AWS_SECRET_ACCESS_KEY.value: "secret_access_key",
            },
            "format": ResponseFormat.json,
        },
    )
    yield sc


@pytest.fixture(scope="function")
def storage_config_default_local(db: Session) -> Generator:
    """
    Create and yield the default local storage config.
    """
    sc = _create_local_default_storage(db)
    yield sc


@pytest.fixture(scope="function")
def set_active_storage_s3(db) -> None:
    ApplicationConfig.create_or_update(
        db,
        data={
            "api_set": {
                "storage": {"active_default_storage_type": StorageType.s3.value}
            }
        },
    )


@pytest.fixture(scope="function")
def property_a(db) -> Generator:
    prop_a = Property.create(
        db=db,
        data=PropertySchema(
            name="New Property",
            type=PropertyType.website,
            experiences=[],
            messaging_templates=[],
            paths=["test"],
        ).model_dump(),
    )
    yield prop_a
    prop_a.delete(db=db)


@pytest.fixture(scope="function")
def property_b(db: Session) -> Generator:
    prop_b = Property.create(
        db=db,
        data=PropertySchema(
            name="New Property b",
            type=PropertyType.website,
            experiences=[],
            messaging_templates=[],
            paths=[],
        ).model_dump(),
    )
    yield prop_b
    prop_b.delete(db=db)


@pytest.fixture(scope="function")
def messaging_template_with_property_disabled(db: Session, property_a) -> Generator:
    template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    content = {
        "subject": "Here is your code __CODE__",
        "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
    }
    data = {
        "content": content,
        "properties": [{"id": property_a.id, "name": property_a.name}],
        "is_enabled": False,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_no_property_disabled(db: Session) -> Generator:
    template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    content = {
        "subject": "Here is your code __CODE__",
        "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
    }
    data = {
        "content": content,
        "properties": [],
        "is_enabled": False,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_no_property(db: Session) -> Generator:
    template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    content = {
        "subject": "Here is your code __CODE__",
        "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
    }
    data = {
        "content": content,
        "properties": [],
        "is_enabled": True,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_subject_identity_verification(
    db: Session, property_a
) -> Generator:
    template_type = MessagingActionType.SUBJECT_IDENTITY_VERIFICATION.value
    content = {
        "subject": "Here is your code __CODE__",
        "body": "Use code __CODE__ to verify your identity, you have __MINUTES__ minutes!",
    }
    data = {
        "content": content,
        "properties": [{"id": property_a.id, "name": property_a.name}],
        "is_enabled": True,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_template_privacy_request_receipt(db: Session, property_a) -> Generator:
    template_type = MessagingActionType.PRIVACY_REQUEST_RECEIPT
    content = {
        "subject": "Your request has been received.",
        "body": "Stay tuned!",
    }
    data = {
        "content": content,
        "properties": [{"id": property_a.id, "name": property_a.name}],
        "is_enabled": True,
        "type": template_type,
    }
    messaging_template = MessagingTemplate.create(
        db=db,
        data=data,
    )
    yield messaging_template
    messaging_template.delete(db)


@pytest.fixture(scope="function")
def messaging_config(db: Session) -> Generator:
    name = str(uuid4())
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_mailgun_messaging_config",
            "service_type": MessagingServiceType.mailgun.value,
            "details": {
                MessagingServiceDetails.API_VERSION.value: "v3",
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.IS_EU_DOMAIN.value: False,
            },
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.MAILGUN_API_KEY.value: "12984r70298r"
        },
    )
    yield messaging_config
    messaging_config.delete(db)


@pytest.fixture(scope="function")
def messaging_config_twilio_email(db: Session) -> Generator:
    name = str(uuid4())
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_twilio_email_config",
            "service_type": MessagingServiceType.twilio_email.value,
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.TWILIO_API_KEY.value: "123489ctynpiqurwfh"
        },
    )
    yield messaging_config
    messaging_config.delete(db)


@pytest.fixture(scope="function")
def messaging_config_twilio_sms(db: Session) -> Generator:
    name = str(uuid4())
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": name,
            "key": "my_twilio_sms_config",
            "service_type": MessagingServiceType.twilio_text.value,
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.TWILIO_ACCOUNT_SID.value: "23rwrfwxwef",
            MessagingServiceSecrets.TWILIO_AUTH_TOKEN.value: "23984y29384y598432",
            MessagingServiceSecrets.TWILIO_MESSAGING_SERVICE_SID.value: "2ieurnoqw",
        },
    )
    yield messaging_config
    messaging_config.delete(db)


@pytest.fixture(scope="function")
def messaging_config_mailchimp_transactional(db: Session) -> Generator:
    messaging_config = MessagingConfig.create(
        db=db,
        data={
            "name": str(uuid4()),
            "key": "my_mailchimp_transactional_messaging_config",
            "service_type": MessagingServiceType.mailchimp_transactional,
            "details": {
                MessagingServiceDetails.DOMAIN.value: "some.domain",
                MessagingServiceDetails.EMAIL_FROM.value: "test@example.com",
            },
        },
    )
    messaging_config.set_secrets(
        db=db,
        messaging_secrets={
            MessagingServiceSecrets.MAILCHIMP_TRANSACTIONAL_API_KEY.value: "12984r70298r"
        },
    )
    yield messaging_config
    messaging_config.delete(db)


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
def pre_approval_webhooks(
    db: Session,
    https_connection_config,
) -> Generator:
    pre_approval_webhook = PreApprovalWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "name": str(uuid4()),
            "key": "pre_approval_webhook",
        },
    )
    pre_approval_webhook_two = PreApprovalWebhook.create(
        db=db,
        data={
            "connection_config_id": https_connection_config.id,
            "name": str(uuid4()),
            "key": "pre_approval_webhook_2",
        },
    )
    db.commit()
    yield [pre_approval_webhook, pre_approval_webhook_two]
    try:
        pre_approval_webhook.delete(db)
    except ObjectDeletedError:
        pass
    try:
        pre_approval_webhook_two.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def access_and_erasure_policy(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    access_and_erasure_policy = Policy.create(
        db=db,
        data={
            "name": "example access and erasure policy",
            "key": "example_access_erasure_policy",
            "client_id": oauth_client.id,
        },
    )
    access_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule",
            "policy_id": access_and_erasure_policy.id,
            "storage_destination_id": storage_config.id,
        },
    )
    access_rule_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user").value,
            "rule_id": access_rule.id,
        },
    )
    erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "Erasure Rule",
            "policy_id": access_and_erasure_policy.id,
            "masking_strategy": {
                "strategy": "null_rewrite",
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
    yield access_and_erasure_policy
    try:
        access_rule_target.delete(db)
        erasure_rule_target.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_rule.delete(db)
        erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        access_and_erasure_policy.delete(db)
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
def biquery_erasure_policy(
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

    user_name_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": erasure_rule.id,
        },
    )
    street_address_target = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.address.street").value,
            "rule_id": erasure_rule.id,
        },
    )
    yield erasure_policy
    try:
        user_name_target.delete(db)
        street_address_target.delete(db)
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
                "strategy": StringRewriteMaskingStrategy.name,
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
                "strategy": NullMaskingStrategy.name,
                "configuration": {},
            },
        },
    )

    # TODO set masking strategy in Rule.create() call above, once more masking strategies beyond NULL_REWRITE are supported.
    second_erasure_rule.masking_strategy = {
        "strategy": StringRewriteMaskingStrategy.name,
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
def erasure_policy_all_categories(
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

    filtered_categories = get_user_data_categories()
    rule_targets = []

    for category in filtered_categories:
        rule_targets.append(
            RuleTarget.create(
                db=db,
                data={
                    "client_id": oauth_client.id,
                    "data_category": category,
                    "rule_id": erasure_rule.id,
                },
            )
        )
    yield erasure_policy
    try:
        for rule_target in rule_targets:
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
def empty_policy(
    db: Session,
    oauth_client: ClientDetail,
) -> Generator:
    policy = Policy.create(
        db=db,
        data={
            "name": "example empty policy",
            "key": "example_empty_policy",
            "client_id": oauth_client.id,
        },
    )
    yield policy
    try:
        policy.delete(db)
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
            "execution_timeframe": 7,
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
def consent_automation() -> Generator:
    consentable_items = [
        {
            "type": "Channel",
            "external_id": 1,
            "name": "Marketing channel (email)",
            "children": [
                {
                    "type": "Message type",
                    "external_id": 1,
                    "name": "Weekly Ads",
                }
            ],
        }
    ]

    ConsentAutomation.create_or_update(
        db,
        data={
            "connection_config_id": connection_config.id,
            "consentable_items": consentable_items,
        },
    )


@pytest.fixture(scope="function")
def consent_policy(
    db: Session,
    oauth_client: ClientDetail,
    storage_config: StorageConfig,
) -> Generator:
    """Consent policies only need a ConsentRule attached - no RuleTargets necessary"""
    consent_request_policy = Policy.create(
        db=db,
        data={
            "name": "example consent request policy",
            "key": "example_consent_request_policy",
            "client_id": oauth_client.id,
        },
    )

    consent_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.consent.value,
            "client_id": oauth_client.id,
            "name": "Consent Request Rule",
            "policy_id": consent_request_policy.id,
        },
    )

    yield consent_request_policy
    try:
        consent_request_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        consent_request_policy.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def policy_local_storage(
    db: Session,
    oauth_client: ClientDetail,
    storage_config_local: StorageConfig,
) -> Generator:
    """
    A basic example policy fixture that uses a local storage config
    in cases where end-to-end request execution must actually succeed
    """
    access_request_policy = Policy.create(
        db=db,
        data={
            "name": "example access request policy",
            "key": "example_access_request_policy",
            "client_id": oauth_client.id,
            "execution_timeframe": 7,
        },
    )

    access_request_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "client_id": oauth_client.id,
            "name": "Access Request Rule",
            "policy_id": access_request_policy.id,
            "storage_destination_id": storage_config_local.id,
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
                "strategy": StringRewriteMaskingStrategy.name,
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
                "strategy": StringRewriteMaskingStrategy.name,
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
def erasure_policy_string_rewrite_name_and_email(
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

    string_erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "string rewrite erasure rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": StringRewriteMaskingStrategy.name,
                "configuration": {"rewrite_value": "MASKED"},
            },
        },
    )

    email_erasure_rule = Rule.create(
        db=db,
        data={
            "action_type": ActionType.erasure.value,
            "client_id": oauth_client.id,
            "name": "email rewrite erasure rule rule",
            "policy_id": erasure_policy.id,
            "masking_strategy": {
                "strategy": RandomStringRewriteMaskingStrategy.name,
                "configuration": {
                    "length": 20,
                    "format_preservation": {"suffix": "@email.com"},
                },
            },
        },
    )

    erasure_rule_target_name = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.name").value,
            "rule_id": string_erasure_rule.id,
        },
    )

    erasure_rule_target_email = RuleTarget.create(
        db=db,
        data={
            "client_id": oauth_client.id,
            "data_category": DataCategory("user.contact.email").value,
            "rule_id": email_erasure_rule.id,
        },
    )

    yield erasure_policy
    try:
        erasure_rule_target_name.delete(db)
    except ObjectDeletedError:
        pass
    try:
        erasure_rule_target_email.delete(db)
    except ObjectDeletedError:
        pass
    try:
        string_erasure_rule.delete(db)
    except ObjectDeletedError:
        pass
    try:
        email_erasure_rule.delete(db)
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
                "strategy": HmacMaskingStrategy.name,
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
    email_identity: Optional[str] = "test@example.com",
    phone_identity: Optional[str] = "+12345678910",
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
    identity_kwargs = {"email": email_identity}
    pr.cache_identity(identity_kwargs)
    pr.persist_identity(
        db=db,
        identity=Identity(
            email=email_identity,
            phone_number=phone_identity,
        ),
    )
    return pr


@pytest.fixture(scope="function")
def privacy_request(
    db: Session, policy: Policy
) -> Generator[PrivacyRequest, None, None]:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def soft_deleted_privacy_request(
    db: Session,
    policy: Policy,
    application_user: FidesUser,
) -> Generator[PrivacyRequest, None, None]:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    privacy_request.soft_delete(db, application_user.id)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def bulk_privacy_requests_with_various_identities(db: Session, policy: Policy) -> None:
    num_records = 2000000  # 2 million
    for i in range(num_records):
        random_email = generate_random_email()
        random_phone_number = generate_random_phone_number()
        _create_privacy_request_for_policy(
            db,
            policy,
            PrivacyRequestStatus.in_processing,
            random_email,
            random_phone_number,
        )
    yield
    for request in db.query(PrivacyRequest):
        request.delete(db)


@pytest.fixture(scope="function")
def request_task(db: Session, privacy_request) -> RequestTask:
    root_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": "complete",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__ROOT__:__ROOT__",
            "dataset_name": "__ROOT__",
            "collection_name": "__ROOT__",
            "upstream_tasks": [],
            "downstream_tasks": ["test_dataset:test_collection"],
            "all_descendant_tasks": [
                "test_dataset:test_collection",
                "__TERMINATE__:__TERMINATE__",
            ],
        },
    )
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "test_dataset:test_collection",
            "dataset_name": "test_dataset",
            "collection_name": "test_collection",
            "upstream_tasks": ["__ROOT__:__ROOT__"],
            "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
            "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
        },
    )
    end_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.access,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__TERMINATE__:__TERMINATE__",
            "dataset_name": "__TERMINATE__",
            "collection_name": "__TERMINATE__",
            "upstream_tasks": ["test_dataset:test_collection"],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
        },
    )
    yield request_task

    try:
        end_task.delete(db).delete(db)
    except ObjectDeletedError:
        pass
    try:
        request_task.delete(db)
    except ObjectDeletedError:
        pass
    try:
        root_task.delete(db)
    except ObjectDeletedError:
        pass


@pytest.fixture(scope="function")
def erasure_request_task(db: Session, privacy_request) -> RequestTask:
    root_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.erasure,
            "status": "complete",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__ROOT__:__ROOT__",
            "dataset_name": "__ROOT__",
            "collection_name": "__ROOT__",
            "upstream_tasks": [],
            "downstream_tasks": ["test_dataset:test_collection"],
            "all_descendant_tasks": [
                "test_dataset:test_collection",
                "__TERMINATE__:__TERMINATE__",
            ],
        },
    )
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.erasure,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "test_dataset:test_collection",
            "dataset_name": "test_dataset",
            "collection_name": "test_collection",
            "upstream_tasks": ["__ROOT__:__ROOT__"],
            "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
            "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
        },
    )
    end_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.erasure,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__TERMINATE__:__TERMINATE__",
            "dataset_name": "__TERMINATE__",
            "collection_name": "__TERMINATE__",
            "upstream_tasks": ["test_dataset:test_collection"],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
        },
    )
    yield request_task
    end_task.delete(db)
    request_task.delete(db)
    root_task.delete(db)


@pytest.fixture(scope="function")
def consent_request_task(db: Session, privacy_request) -> RequestTask:
    root_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.consent,
            "status": "complete",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__ROOT__:__ROOT__",
            "dataset_name": "__ROOT__",
            "collection_name": "__ROOT__",
            "upstream_tasks": [],
            "downstream_tasks": ["test_dataset:test_collection"],
            "all_descendant_tasks": [
                "test_dataset:test_collection",
                "__TERMINATE__:__TERMINATE__",
            ],
        },
    )
    request_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.consent,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "test_dataset:test_collection",
            "dataset_name": "test_dataset",
            "collection_name": "test_collection",
            "upstream_tasks": ["__ROOT__:__ROOT__"],
            "downstream_tasks": ["__TERMINATE__:__TERMINATE__"],
            "all_descendant_tasks": ["__TERMINATE__:__TERMINATE__"],
        },
    )
    end_task = RequestTask.create(
        db,
        data={
            "action_type": ActionType.consent,
            "status": "pending",
            "privacy_request_id": privacy_request.id,
            "collection_address": "__TERMINATE__:__TERMINATE__",
            "dataset_name": "__TERMINATE__",
            "collection_name": "__TERMINATE__",
            "upstream_tasks": ["test_dataset:test_collection"],
            "downstream_tasks": [],
            "all_descendant_tasks": [],
        },
    )
    yield request_task
    end_task.delete(db)
    request_task.delete(db)
    root_task.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_erasure_policy(
    db: Session, erasure_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        erasure_policy,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_consent_policy(
    db: Session, consent_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        consent_policy,
    )
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_custom_fields(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
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
    privacy_request.persist_custom_privacy_request_fields(
        db=db,
        custom_privacy_request_fields={
            "first_name": CustomPrivacyRequestField(label="First name", value="John"),
            "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
        },
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_custom_array_fields(
    db: Session, policy: Policy
) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
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
    privacy_request.persist_custom_privacy_request_fields(
        db=db,
        custom_privacy_request_fields={
            "device_ids": CustomPrivacyRequestField(
                label="Device Ids", value=["device_1", "device_2", "device_3"]
            ),
        },
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_email_identity(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
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
    privacy_request.persist_identity(
        db=db,
        identity=Identity(email="customer-1@example.com"),
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_with_custom_identities(
    db: Session, policy: Policy
) -> PrivacyRequest:
    privacy_request = PrivacyRequest.create(
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
    privacy_request.persist_identity(
        db=db,
        identity=Identity(loyalty_id=LabeledIdentity(label="Loyalty ID", value="CH-1")),
    )
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_requires_input(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
    )
    privacy_request.status = PrivacyRequestStatus.requires_input
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_awaiting_consent_email_send(
    db: Session, consent_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        consent_policy,
    )
    privacy_request.status = PrivacyRequestStatus.awaiting_email_send
    privacy_request.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def privacy_request_awaiting_erasure_email_send(
    db: Session, erasure_policy: Policy
) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        erasure_policy,
    )
    privacy_request.status = PrivacyRequestStatus.awaiting_email_send
    privacy_request.save(db)
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
def privacy_request_status_approved(db: Session, policy: Policy) -> PrivacyRequest:
    privacy_request = _create_privacy_request_for_policy(
        db,
        policy,
        PrivacyRequestStatus.approved,
    )
    yield privacy_request
    privacy_request.delete(db)


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
        identity=Identity(**identity_kwargs),
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
def privacy_notice_2(db: Session) -> Generator:
    template = PrivacyNoticeTemplate.create(
        db,
        check_name=False,
        data={
            "name": "example privacy notice 2",
            "notice_key": "example_privacy_notice_2",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice 2",
            "notice_key": "example_privacy_notice_2",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "origin": template.id,
            "translations": [
                {
                    "language": "en",
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )

    yield privacy_notice
    for translation in privacy_notice.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)
    privacy_notice.delete(db)


@pytest.fixture(scope="function")
def privacy_notice(db: Session) -> Generator:
    template = PrivacyNoticeTemplate.create(
        db,
        check_name=False,
        data={
            "name": "example privacy notice",
            "notice_key": "example_privacy_notice_1",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice",
            "notice_key": "example_privacy_notice_1",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "origin": template.id,
            "translations": [
                {
                    "language": "en",
                    "title": "Example privacy notice",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )

    yield privacy_notice
    for translation in privacy_notice.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)
    privacy_notice.delete(db)


@pytest.fixture(scope="function")
def served_notice_history(
    db: Session, privacy_notice, fides_user_provided_identity
) -> Generator:
    pref_1 = ServedNoticeHistory.create(
        db=db,
        data={
            "acknowledge_mode": False,
            "serving_component": ServingComponent.overlay,
            "privacy_notice_history_id": privacy_notice.privacy_notice_history_id,
            "email": "test@example.com",
            "hashed_email": ConsentIdentitiesMixin.hash_value("test@example.com"),
            "served_notice_history_id": "ser_12345",
        },
        check_name=False,
    )
    yield pref_1
    pref_1.delete(db)


@pytest.fixture(scope="function")
def privacy_notice_us_ca_provide(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_ca provide",
            "notice_key": "example_privacy_notice_us_ca_provide",
            # no origin on this privacy notice to help
            # cover edge cases due to column nullability
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["essential"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_ca provide",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_preference_history_us_ca_provide(
    db: Session,
    privacy_notice_us_ca_provide,
    privacy_preference_history,
    privacy_experience_privacy_center,
    served_notice_history,
) -> Generator:
    preference_history_record = PrivacyPreferenceHistory.create(
        db=db,
        data={
            "anonymized_ip_address": "92.158.1.0",
            "email": "test@email.com",
            "method": "button",
            "privacy_experience_config_history_id": privacy_experience_privacy_center.experience_config.translations[
                0
            ].privacy_experience_config_history_id,
            "preference": "opt_in",
            "privacy_notice_history_id": privacy_notice_us_ca_provide.translations[
                0
            ].privacy_notice_history_id,
            "request_origin": "privacy_center",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
            "user_geography": "us_ca",
            "url_recorded": "https://example.com/privacy_center",
            "served_notice_history_id": served_notice_history.served_notice_history_id,
        },
        check_name=False,
    )

    yield preference_history_record
    preference_history_record.delete(db)


@pytest.fixture(scope="function")
def privacy_notice_us_co_third_party_sharing(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_co third_party_sharing",
            "notice_key": "example_privacy_notice_us_co_third_party_sharing",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_co third_party_sharing",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_notice_us_co_provide_service_operations(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_co provide.service.operations",
            "notice_key": "example_privacy_notice_us_co_provide.service.operations",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["essential.service.operations"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_co provide.service.operations",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_experience_france_tcf_overlay(
    db: Session, experience_config_tcf_overlay
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.fr,
            "experience_config_id": experience_config_tcf_overlay.id,
        },
    )

    yield privacy_experience

    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_france_overlay(
    db: Session, experience_config_banner_and_modal
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.fr,
            "experience_config_id": experience_config_banner_and_modal.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def privacy_notice_fr_provide_service_frontend_only(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice us_co provide.service.operations",
            "notice_key": "example_privacy_notice_us_co_provide.service.operations",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["essential.service"],
            "enforcement_level": EnforcementLevel.frontend,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice us_co provide.service.operations",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_notice_eu_cy_provide_service_frontend_only(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice eu_cy provide.service.operations",
            "notice_key": "example_privacy_notice_eu_cy_provide.service.operations",
            "consent_mechanism": ConsentMechanism.opt_out,
            "data_uses": ["essential.service"],
            "enforcement_level": EnforcementLevel.frontend,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice eu_cy provide.service.operations",
                    "description": "a sample privacy notice configuration",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def privacy_preference_history_fr_provide_service_frontend_only(
    db: Session,
    privacy_notice_fr_provide_service_frontend_only,
    privacy_experience_privacy_center,
    served_notice_history,
) -> Generator:
    preference_history_record = PrivacyPreferenceHistory.create(
        db=db,
        data={
            "anonymized_ip_address": "92.158.1.0",
            "email": "test@email.com",
            "method": "button",
            "privacy_experience_config_history_id": privacy_experience_privacy_center.experience_config.translations[
                0
            ].privacy_experience_config_history_id,
            "preference": "opt_out",
            "privacy_notice_history_id": privacy_notice_fr_provide_service_frontend_only.translations[
                0
            ].privacy_notice_history_id,
            "request_origin": "privacy_center",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
            "user_geography": "fr_idg",
            "url_recorded": "https://example.com/privacy_center",
            "served_notice_history_id": served_notice_history.served_notice_history_id,
        },
        check_name=False,
    )

    yield preference_history_record
    preference_history_record.delete(db)


@pytest.fixture(scope="function")
def ctl_dataset(db: Session, example_datasets):
    ds = Dataset(
        fides_key="postgres_example_subscriptions_dataset",
        organization_fides_key="default_organization",
        name="Postgres Example Subscribers Dataset",
        description="Example Postgres dataset created in test fixtures",
        collections=[
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
    )
    dataset = CtlDataset(**ds.model_dump(mode="json"))
    db.add(dataset)
    db.commit()
    yield dataset
    dataset.delete(db)


@pytest.fixture(scope="function")
def unlinked_dataset(db: Session):
    ds = Dataset(
        fides_key="unlinked_dataset",
        organization_fides_key="default_organization",
        name="Unlinked Dataset",
        description="Example dataset created in test fixtures",
        collections=[
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
    )
    dataset = CtlDataset(**ds.model_dump(mode="json"))
    db.add(dataset)
    db.commit()
    yield dataset
    dataset.delete(db)


@pytest.fixture(scope="function")
def linked_dataset(db: Session, connection_config: ConnectionConfig) -> Generator:
    ds = Dataset(
        fides_key="linked_dataset",
        organization_fides_key="default_organization",
        name="Linked Dataset",
        description="Example dataset created in test fixtures",
        collections=[
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
    )
    dataset = CtlDataset(**ds.model_dump(mode="json"))
    db.add(dataset)
    db.commit()
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "postgres_example_subscriptions_dataset",
            "ctl_dataset_id": dataset.id,
        },
    )

    yield dataset
    dataset_config.delete(db)
    dataset.delete(db)


@pytest.fixture(scope="function")
def dataset_config(
    connection_config: ConnectionConfig,
    ctl_dataset,
    db: Session,
) -> Generator:
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "postgres_example_subscriptions_dataset",
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    yield dataset_config
    dataset_config.delete(db)


@pytest.fixture(scope="function")
def dataset_config_preview(
    connection_config: ConnectionConfig, db: Session, ctl_dataset
) -> Generator:
    ctl_dataset.fides_key = "postgres"
    db.add(ctl_dataset)
    db.commit()
    dataset_config = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": "postgres",
            "ctl_dataset_id": ctl_dataset.id,
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
        "data/dataset/email_dataset.yml",
        "data/dataset/remote_fides_example_test_dataset.yml",
        "data/dataset/dynamodb_example_test_dataset.yml",
        "data/dataset/postgres_example_test_extended_dataset.yml",
        "data/dataset/google_cloud_sql_mysql_example_test_dataset.yml",
        "data/dataset/google_cloud_sql_postgres_example_test_dataset.yml",
        "data/dataset/scylladb_example_test_dataset.yml",
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
            "email_address": "test.user@ethyca.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    oauth_client.user_id = user.id
    oauth_client.save(db=db)
    yield user
    user.delete(db=db)


@pytest.fixture(scope="function")
def short_redis_cache_expiration():
    original_value: int = CONFIG.redis.default_ttl_seconds
    CONFIG.redis.default_ttl_seconds = (
        1  # Set redis cache to expire very quickly for testing purposes
    )
    yield CONFIG
    CONFIG.redis.default_ttl_seconds = original_value


@pytest.fixture(scope="function")
def user_registration_opt_out(db: Session) -> UserRegistration:
    """Adds a UserRegistration record with `opt_in` as False."""
    return create_user_registration(db, opt_in=False)


@pytest.fixture(scope="function")
def user_registration_opt_in(db: Session) -> UserRegistration:
    """Adds a UserRegistration record with `opt_in` as True."""
    return create_user_registration(db, opt_in=True)


def create_user_registration(db: Session, opt_in: bool = False) -> UserRegistration:
    """Adds a UserRegistration record."""
    return UserRegistration.create(
        db=db,
        data={
            "user_email": "user@example.com",
            "user_organization": "Example Org.",
            "analytics_id": "example-analytics-id",
            "opt_in": opt_in,
        },
    )


@pytest.fixture(scope="function")
def test_fides_client(
    fides_connector_example_secrets: Dict[str, str], api_client
) -> FidesClient:
    return FidesClient(
        fides_connector_example_secrets["uri"],
        fides_connector_example_secrets["username"],
        fides_connector_example_secrets["password"],
        fides_connector_example_secrets["polling_timeout"],
    )


@pytest.fixture(scope="function")
def authenticated_fides_client(
    test_fides_client: FidesClient,
) -> FidesClient:
    test_fides_client.login()
    return test_fides_client


@pytest.fixture(scope="function")
def system_manager(db: Session, system) -> System:
    user = FidesUser.create(
        db=db,
        data={
            "username": "test_system_manager_user",
            "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
            "email_address": "system-manager.user@ethyca.com",
        },
    )
    client = ClientDetail(
        hashed_secret="thisisatest",
        salt="thisisstillatest",
        scopes=[],
        roles=[VIEWER],
        user_id=user.id,
        systems=[system.id],
    )

    FidesUserPermissions.create(db=db, data={"user_id": user.id, "roles": [VIEWER]})

    db.add(client)
    db.commit()
    db.refresh(client)

    user.set_as_system_manager(db, system)
    yield user
    try:
        user.remove_as_system_manager(db, system)
    except (SystemManagerException, StaleDataError):
        pass
    user.delete(db)


@pytest.fixture(scope="function")
def empty_provided_identity(db):
    provided_identity = ProvidedIdentity.create(db, data={"field_name": "email"})
    yield provided_identity
    provided_identity.delete(db)


@pytest.fixture(scope="function")
def custom_provided_identity(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "customer_id",
        "field_label": "Customer ID",
        "hashed_value": ProvidedIdentity.hash_value("123"),
        "encrypted_value": {"value": "123"},
    }
    provided_identity = ProvidedIdentity.create(
        db,
        data=provided_identity_data,
    )
    yield provided_identity
    provided_identity.delete(db=db)


@pytest.fixture(scope="function")
def provided_identity_value():
    return "test@email.com"


@pytest.fixture(scope="function")
def provided_identity_and_consent_request(
    db,
    provided_identity_value,
):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "email",
        "hashed_value": ProvidedIdentity.hash_value(provided_identity_value),
        "encrypted_value": {"value": provided_identity_value},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    consent_request_data = {
        "provided_identity_id": provided_identity.id,
        "source": PrivacyRequestSource.privacy_center,
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    yield provided_identity, consent_request
    provided_identity.delete(db=db)
    consent_request.delete(db=db)


@pytest.fixture(scope="function")
def provided_identity_and_consent_request_with_custom_fields(
    db,
    provided_identity_and_consent_request,
):
    _, consent_request = provided_identity_and_consent_request
    consent_request.persist_custom_privacy_request_fields(
        db=db,
        custom_privacy_request_fields={
            "first_name": CustomPrivacyRequestField(label="First name", value="John"),
            "last_name": CustomPrivacyRequestField(label="Last name", value="Doe"),
        },
    )
    return consent_request


@pytest.fixture(scope="function")
def fides_user_provided_identity(db):
    provided_identity_data = {
        "privacy_request_id": None,
        "field_name": "fides_user_device_id",
        "hashed_value": ProvidedIdentity.hash_value(
            "051b219f-20e4-45df-82f7-5eb68a00889f"
        ),
        "encrypted_value": {"value": "051b219f-20e4-45df-82f7-5eb68a00889f"},
    }
    provided_identity = ProvidedIdentity.create(db, data=provided_identity_data)

    yield provided_identity
    provided_identity.delete(db=db)


@pytest.fixture(scope="function")
def fides_user_provided_identity_and_consent_request(db, fides_user_provided_identity):
    consent_request_data = {
        "provided_identity_id": fides_user_provided_identity.id,
    }
    consent_request = ConsentRequest.create(db, data=consent_request_data)

    yield fides_user_provided_identity, consent_request
    fides_user_provided_identity.delete(db=db)
    consent_request.delete(db=db)


@pytest.fixture(scope="function")
def executable_consent_request(
    db,
    provided_identity_and_consent_request,
    consent_policy,
):
    provided_identity = provided_identity_and_consent_request[0]
    consent_request = provided_identity_and_consent_request[1]
    privacy_request = _create_privacy_request_for_policy(
        db,
        consent_policy,
    )
    consent_request.privacy_request_id = privacy_request.id
    consent_request.save(db)
    provided_identity.privacy_request_id = privacy_request.id
    provided_identity.save(db)
    yield privacy_request
    privacy_request.delete(db)


@pytest.fixture(scope="function")
def current_privacy_preference(
    db,
    privacy_notice,
    privacy_experience_privacy_center,
    served_notice_history,
):
    pref = CurrentPrivacyPreference.create(
        db=db,
        data={
            "email": "test@email.com",
            "hashed_email": ConsentIdentitiesMixin.hash_value("test@email.com"),
            "preferences": {
                "purpose_consent_preferences": [],
                "purpose_legitimate_interests_preferences": [],
                "vendor_consent_preferences": [],
                "vendor_legitimate_interests_preferences": [],
                "special_feature_preferences": [],
                "preferences": [
                    {
                        "privacy_notice_history_id": privacy_notice.histories[0].id,
                        "preference": "opt_out",
                    }
                ],
                "special_purpose_preferences": [],
                "feature_preferences": [],
                "system_consent_preferences": [],
                "system_legitimate_interests_preferences": [],
            },
        },
    )

    yield pref

    pref.delete(db)


@pytest.fixture(scope="function")
def privacy_preference_history(
    db,
    privacy_notice,
    privacy_experience_privacy_center,
    served_notice_history,
):
    privacy_notice_history = privacy_notice.translations[0].histories[0]

    preference_history_record = PrivacyPreferenceHistory.create(
        db=db,
        data={
            "anonymized_ip_address": "92.158.1.0",
            "email": "test@email.com",
            "method": "button",
            "privacy_experience_config_history_id": privacy_experience_privacy_center.experience_config.translations[
                0
            ].privacy_experience_config_history_id,
            "preference": "opt_out",
            "privacy_notice_history_id": privacy_notice_history.id,
            "request_origin": "privacy_center",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/324.42 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/425.24",
            "user_geography": "us_ca",
            "url_recorded": "https://example.com/privacy_center",
            "served_notice_history_id": served_notice_history.served_notice_history_id,
        },
        check_name=False,
    )
    yield preference_history_record
    preference_history_record.delete(db)


@pytest.fixture(scope="function")
def anonymous_consent_records(
    db,
    fides_user_provided_identity_and_consent_request,
):
    (
        provided_identity,
        consent_request,
    ) = fides_user_provided_identity_and_consent_request
    consent_request.cache_identity_verification_code("abcdefg")

    consent_data = [
        {
            "data_use": "email",
            "data_use_description": None,
            "opt_in": True,
        },
        {
            "data_use": "location",
            "data_use_description": "Location data",
            "opt_in": False,
        },
    ]

    records = []
    for data in deepcopy(consent_data):
        data["provided_identity_id"] = provided_identity.id
        records.append(Consent.create(db, data=data))

    yield records

    for record in records:
        record.delete(db)


@pytest.fixture(scope="function")
def consent_records(
    db,
    provided_identity_and_consent_request,
):
    provided_identity, consent_request = provided_identity_and_consent_request
    consent_request.cache_identity_verification_code("abcdefg")

    consent_data = [
        {
            "data_use": "email",
            "data_use_description": None,
            "opt_in": True,
        },
        {
            "data_use": "location",
            "data_use_description": "Location data",
            "opt_in": False,
        },
    ]

    records = []
    for data in deepcopy(consent_data):
        data["provided_identity_id"] = provided_identity.id
        records.append(Consent.create(db, data=data))

    yield records

    for record in records:
        record.delete(db)


@pytest.fixture(scope="function")
def experience_config_modal(db: Session) -> Generator:
    exp = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "modal",
            "regions": [PrivacyNoticeRegion.it],
            "disabled": False,
            "name": "Experience Config Modal",
            "translations": [
                {
                    "language": "en",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Control your privacy",
                    "accept_button_label": "Accept all",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )
    yield exp
    for translation in exp.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    exp.delete(db)


@pytest.fixture(scope="function")
def experience_config_privacy_center(db: Session) -> Generator:
    exp = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "privacy_center",
            "name": "Privacy Center config",
            "translations": [
                {
                    "language": "en",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Control your privacy",
                    "accept_button_label": "Accept all",
                    "description": "user&#x27;s description &lt;script /&gt;",
                }
            ],
        },
    )
    yield exp
    for translation in exp.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    exp.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_privacy_center(
    db: Session, experience_config_privacy_center
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.us_co,
            "experience_config_id": experience_config_privacy_center.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def experience_config_banner_and_modal(db: Session) -> Generator:
    config = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "banner_and_modal",
            "allow_language_selection": False,
            "name": "Banner and modal config",
            "translations": [
                {
                    "language": "en",
                    "accept_button_label": "Accept all",
                    "acknowledge_button_label": "Confirm",
                    "banner_description": "You can accept, reject, or manage your preferences in detail.",
                    "banner_title": "Manage Your Consent",
                    "description": "On this page you can opt in and out of these data uses cases",
                    "privacy_preferences_link_label": "Manage preferences",
                    "modal_link_label": "Manage my consent preferences",
                    "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                    "privacy_policy_url": "https://example.com/privacy",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Manage your consent",
                }
            ],
        },
    )

    yield config
    for translation in config.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    config.delete(db)


@pytest.fixture(scope="function")
def experience_config_tcf_overlay(db: Session) -> Generator:
    config = PrivacyExperienceConfig.create(
        db=db,
        data={
            "component": "tcf_overlay",
            "name": "TCF Config",
            "translations": [
                {
                    "language": "en",
                    "privacy_preferences_link_label": "Manage preferences",
                    "modal_link_label": "Manage my consent preferences",
                    "privacy_policy_link_label": "View our company&#x27;s privacy policy",
                    "privacy_policy_url": "https://example.com/privacy",
                    "reject_button_label": "Reject all",
                    "save_button_label": "Save",
                    "title": "Manage your consent",
                    "description": "On this page you can opt in and out of these data uses cases",
                    "accept_button_label": "Accept all",
                    "acknowledge_button_label": "Confirm",
                    "banner_description": "You can accept, reject, or manage your preferences in detail.",
                    "banner_title": "Manage Your Consent",
                }
            ],
        },
    )

    yield config
    for translation in config.translations:
        for history in translation.histories:
            history.delete(db)
        translation.delete(db)

    config.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_overlay(
    db: Session, experience_config_banner_and_modal
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.us_ca,
            "experience_config_id": experience_config_banner_and_modal.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def privacy_experience_privacy_center_france(
    db: Session, experience_config_privacy_center
) -> Generator:
    privacy_experience = PrivacyExperience.create(
        db=db,
        data={
            "region": PrivacyNoticeRegion.fr,
            "experience_config_id": experience_config_privacy_center.id,
        },
    )

    yield privacy_experience
    privacy_experience.delete(db)


@pytest.fixture(scope="function")
def privacy_notice_france(db: Session) -> Generator:
    privacy_notice = PrivacyNotice.create(
        db=db,
        data={
            "name": "example privacy notice",
            "notice_key": "example_privacy_notice",
            "consent_mechanism": ConsentMechanism.opt_in,
            "data_uses": ["marketing.advertising", "third_party_sharing"],
            "enforcement_level": EnforcementLevel.system_wide,
            "translations": [
                {
                    "language": "en",
                    "title": "example privacy notice",
                    "description": "user description",
                }
            ],
        },
    )

    yield privacy_notice


@pytest.fixture(scope="function")
def allow_custom_privacy_request_field_collection_enabled():
    original_value = CONFIG.execution.allow_custom_privacy_request_field_collection
    CONFIG.execution.allow_custom_privacy_request_field_collection = True
    yield
    CONFIG.notifications.send_request_review_notification = original_value


@pytest.fixture(scope="function")
def allow_custom_privacy_request_field_collection_disabled():
    original_value = CONFIG.execution.allow_custom_privacy_request_field_collection
    CONFIG.execution.allow_custom_privacy_request_field_collection = False
    yield
    CONFIG.notifications.send_request_review_notification = original_value


@pytest.fixture(scope="function")
def allow_custom_privacy_request_fields_in_request_execution_enabled():
    original_value = (
        CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution
    )
    CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution = True
    yield
    CONFIG.notifications.allow_custom_privacy_request_fields_in_request_execution = (
        original_value
    )


@pytest.fixture(scope="function")
def allow_custom_privacy_request_fields_in_request_execution_disabled():
    original_value = (
        CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution
    )
    CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution = False
    yield
    CONFIG.notifications.allow_custom_privacy_request_fields_in_request_execution = (
        original_value
    )


@pytest.fixture(scope="function")
def subject_request_download_ui_enabled():
    original_value = CONFIG.security.subject_request_download_ui_enabled
    CONFIG.security.subject_request_download_ui_enabled = True
    yield
    CONFIG.security.subject_request_download_ui_enabled = original_value


@pytest.fixture(scope="function")
def system_with_no_uses(db: Session) -> Generator[System, None, None]:
    system = System.create(
        db=db,
        data={
            "fides_key": f"system_fides_key",
            "name": f"system-{uuid4()}",
            "description": "tcf_relevant_system",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )
    yield system
    db.delete(system)


@pytest.fixture(scope="function")
def tcf_system(db: Session) -> Generator[System, None, None]:
    system = System.create(
        db=db,
        data={
            "fides_key": f"tcf-system_key-f{uuid4()}",
            "vendor_id": "gvl.42",
            "name": f"TCF System Test",
            "description": "My TCF System Description",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Collect data for content performance",
            "system_id": system.id,
            "data_categories": ["user.device.cookie_id"],
            "data_use": "analytics.reporting.content_performance",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "legal_basis_for_processing": "Consent",
            "egress": None,
            "ingress": None,
            "retention_period": "3",
        },
    )

    PrivacyDeclaration.create(
        db=db,
        data={
            "name": "Ensure security, prevent and detect fraud",
            "system_id": system.id,
            "data_categories": ["user"],
            "data_use": "essential.fraud_detection",
            "data_subjects": ["customer"],
            "dataset_references": None,
            "legal_basis_for_processing": "Legitimate interests",
            "egress": None,
            "ingress": None,
            "retention_period": "1",
        },
    )

    db.refresh(system)
    yield system
    db.delete(system)


@pytest.fixture(scope="function")
def ac_system_with_privacy_declaration(db: Session) -> System:
    """Test AC System with privacy declarations - several contrived
    declarations here to assert content that shouldn't show up in the
    TCF experience is suppressed
    """
    system = System.create(
        db=db,
        data={
            "fides_key": f"ac_system{uuid.uuid4()}",
            "vendor_id": "gacp.8",
            "name": f"Test AC System",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    # Valid TCF purpose with consent legal basis
    PrivacyDeclaration.create(
        db=db,
        data={
            "system_id": system.id,
            "data_use": "functional.storage",
            "legal_basis_for_processing": "Consent",
            "features": [
                "Link different devices",  # Feature 2
            ],
        },
    )

    # Separate purpose with legitimate interest which isn't valid for AC systems
    PrivacyDeclaration.create(
        db=db,
        data={
            "system_id": system.id,
            "data_use": "analytics.reporting.content_performance",
            "legal_basis_for_processing": "Legitimate interests",
            "features": [
                "Link different devices",  # Feature 2
            ],
        },
    )

    # Separate purpose with consent legal basis but it is not a TCF data use, so shouldn't show up
    PrivacyDeclaration.create(
        db=db,
        data={
            "system_id": system.id,
            "data_use": "marketing.advertising",
            "legal_basis_for_processing": "Consent",
            "features": [
                "Link different devices",  # Feature 2
            ],
        },
    )
    return system


@pytest.fixture(scope="function")
def ac_system_without_privacy_declaration(db: Session) -> System:
    """Test AC System without privacy declaration"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"ac_system{uuid.uuid4()}",
            "vendor_id": "gacp.100",
            "name": f"Test AC System 2",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    return system


@pytest.fixture(scope="function")
def ac_system_with_invalid_li_declaration(db: Session) -> System:
    """Test AC System with invalid LI declaration only"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"ac_system{uuid.uuid4()}",
            "vendor_id": "gacp.100",
            "name": f"Test AC System 3",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )
    # Separate purpose with legitimate interest which isn't valid for AC systems
    PrivacyDeclaration.create(
        db=db,
        data={
            "system_id": system.id,
            "data_use": "analytics.reporting.content_performance",
            "legal_basis_for_processing": "Legitimate interests",
            "features": [
                "Link different devices",  # Feature 2
            ],
        },
    )

    return system


@pytest.fixture(scope="function")
def ac_system_with_invalid_vi_declaration(db: Session) -> System:
    """Test AC System with vital interests declaration only"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"ac_system{uuid.uuid4()}",
            "vendor_id": "gacp.100",
            "name": f"Test AC System 4",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )
    # Separate purpose with "Vital interests"
    PrivacyDeclaration.create(
        db=db,
        data={
            "system_id": system.id,
            "data_use": "analytics.reporting.content_performance",
            "legal_basis_for_processing": "Vital interests",
            "features": [
                "Link different devices",  # Feature 2
            ],
        },
    )

    return system


# Detailed systems with attributes for TC string testing
# Please don't update them!


@pytest.fixture(scope="function")
def captify_technologies_system(db: Session) -> System:
    """Add system that only has purposes with Consent legal basis"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"captify_{uuid.uuid4()}",
            "vendor_id": "gvl.2",
            "name": f"Captify",
            "description": "Captify is a search intelligence platform that helps brands and advertisers leverage search insights to improve their ad targeting and relevance.",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "uses_profiling": False,
            "legal_basis_for_transfers": ["SCCs"],
        },
    )

    for data_use in [
        "functional.storage",  # Purpose 1
        "marketing.advertising.negative_targeting",  # Purpose 2
        "marketing.advertising.frequency_capping",  # Purpose 2
        "marketing.advertising.first_party.contextual",  # Purpose 2
        "marketing.advertising.profiling",  # Purpose 3
        "marketing.advertising.first_party.targeted",  # Purpose 4
        "marketing.advertising.third_party.targeted",  # Purpose 4
        "analytics.reporting.ad_performance",  # Purpose 7
        "analytics.reporting.campaign_insights",  # Purpose 9
        "functional.service.improve",  # Purpose 10
        "essential.fraud_detection",  # Special Purpose 1
        "essential.service.security"  # Special Purpose 1
        "marketing.advertising.serving",  # Special Purpose 2
    ]:
        # Includes Feature 2, Special Feature 2
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Consent",
                "features": [
                    "Link different devices",
                    "Actively scan device characteristics for identification",
                ],
            },
        )

    db.refresh(system)
    return system


@pytest.fixture(scope="function")
def emerse_system(db: Session) -> System:
    """This system has purposes that are both consent and legitimate interest legal basis"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"emerse{uuid.uuid4()}",
            "vendor_id": "gvl.8",
            "name": f"Emerse",
            "description": "Emerse Sverige AB is a provider of programmatic advertising solutions, offering advertisers and publishers tools to manage and optimize their digital ad campaigns.",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    # Add Consent-related Purposes
    for data_use in [
        "functional.storage",  # Purpose 1
        "marketing.advertising.profiling",  # Purpose 3
        "marketing.advertising.third_party.targeted",  # Purpose 4
        "marketing.advertising.first_party.targeted",  # Purpose 4
    ]:
        # Includes Feature 2, Special Feature 2
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Consent",
                "features": [
                    "Match and combine data from other data sources",  # Feature 1
                    "Link different devices",  # Feature 2
                ],
            },
        )

    # Add Legitimate Interest-related Purposes
    for data_use in [
        "marketing.advertising.negative_targeting",  # Purpose 2
        "marketing.advertising.first_party.contextual",  # Purpose 2
        "marketing.advertising.frequency_capping",  # Purpose 2
        "analytics.reporting.ad_performance",  # Purpose 7
        "analytics.reporting.content_performance",  # Purpose 8
        "analytics.reporting.campaign_insights",  # Purpose 9
        "essential.fraud_detection",  # Special Purpose 1
        "essential.service.security",  # Special Purpose 1
        "marketing.advertising.serving",  # Special Purpose 2
    ]:
        # Includes Feature 2, Special Feature 2
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Legitimate interests",
                "features": [
                    "Match and combine data from other data sources",  # Feature 1
                    "Link different devices",  # Feature 2
                ],
            },
        )

    db.refresh(system)
    return system


@pytest.fixture(scope="function")
def skimbit_system(db):
    """Add system that only has purposes with LI legal basis"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"skimbit{uuid.uuid4()}",
            "vendor_id": "gvl.46",
            "name": f"Skimbit (Skimlinks, Taboola)",
            "description": "Skimbit, a Taboola company, specializes in data-driven advertising and provides tools for brands and advertisers to analyze customer behavior and deliver targeted and personalized ads.",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    # Add Legitimate Interest-related Purposes
    for data_use in [
        "analytics.reporting.ad_performance",  # Purpose 7
        "analytics.reporting.content_performance",  # Purpose 8
        "functional.service.improve",  # Purpose 10
        "essential.service.security"  # Special Purpose 1
        "essential.fraud_detection",  # Special Purpose 1
        "marketing.advertising.serving",  # Special Purpose 2
    ]:
        # Includes Feature 3
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Legitimate interests",
                "features": [
                    "Identify devices based on information transmitted automatically"
                ],
            },
        )
    return system


@pytest.fixture(scope="function")
def purpose_three_consent_publisher_override(db):
    override = TCFPurposeOverride.create(
        db,
        data={
            "purpose": 3,
            "is_included": True,
            "required_legal_basis": "Consent",
        },
    )
    yield override
    override.delete(db)


@pytest.fixture(scope="function")
def served_notice_history(
    db: Session, privacy_notice, fides_user_provided_identity
) -> Generator:
    pref_1 = ServedNoticeHistory.create(
        db=db,
        data={
            "acknowledge_mode": False,
            "serving_component": ServingComponent.overlay,
            "privacy_notice_history_id": privacy_notice.translations[
                0
            ].privacy_notice_history_id,
            "email": "test@example.com",
            "hashed_email": ConsentIdentitiesMixin.hash_value("test@example.com"),
            "served_notice_history_id": "ser_12345",
        },
        check_name=False,
    )
    yield pref_1
    pref_1.delete(db)


@pytest.fixture(scope="function")
def use_dsr_3_0():
    original_value: int = CONFIG.execution.use_dsr_3_0
    CONFIG.execution.use_dsr_3_0 = True
    yield CONFIG
    CONFIG.execution.use_dsr_3_0 = original_value


@pytest.fixture(scope="function")
def use_dsr_2_0():
    original_value: int = CONFIG.execution.use_dsr_3_0
    CONFIG.execution.use_dsr_3_0 = False
    yield CONFIG
    CONFIG.execution.use_dsr_3_0 = original_value


@pytest.fixture()
def postgres_dataset_graph(example_datasets, connection_config):
    dataset_postgres = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)

    dataset_graph = DatasetGraph(*[graph])
    return dataset_graph


@pytest.fixture()
def postgres_and_mongo_dataset_graph(
    example_datasets, connection_config, mongo_connection_config
):
    dataset_postgres = Dataset(**example_datasets[0])
    graph = convert_dataset_to_graph(dataset_postgres, connection_config.key)
    dataset_mongo = Dataset(**example_datasets[1])
    mongo_graph = convert_dataset_to_graph(dataset_mongo, mongo_connection_config.key)
    return DatasetGraph(*[graph, mongo_graph])


@pytest.fixture(scope="function")
def dataset_with_unreachable_collections(
    db: Session, test_fides_org: Organization
) -> Generator[CtlDataset, None, None]:
    dataset = Dataset(
        **{
            "name": "dataset with unreachable collections",
            "fides_key": "dataset_with_unreachable_collections",
            "organization_fides_key": test_fides_org.fides_key,
            "collections": [
                {
                    "name": "login",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "customer_id",
                            "data_categories": ["user.unique_id"],
                        },
                    ],
                    "fides_meta": {"skip_processing": False},
                },
                {
                    "name": "report",
                    "fields": [
                        {
                            "name": "id",
                            "data_categories": ["user.unique_id"],
                        },
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                        },
                    ],
                    "fides_meta": {"skip_processing": False},
                },
            ],
        },
    )

    yield dataset


@pytest.fixture(scope="function")
def dataset_graph_with_unreachable_collections(
    dataset_with_unreachable_collections: Dataset,
) -> Generator[DatasetGraph, None, None]:
    graph = convert_dataset_to_graph(
        dataset_with_unreachable_collections, "unreachable-dataset-test"
    )
    dataset_graph = DatasetGraph(graph)
    yield dataset_graph
