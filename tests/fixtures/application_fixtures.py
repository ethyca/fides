import logging
import uuid
from typing import Dict, Generator
from uuid import uuid4

import pydash
import pytest
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from toml import load as load_toml

from fides.api.common_exceptions import SystemManagerException
from fides.api.models.application_config import ApplicationConfig
from fides.api.models.client import ClientDetail
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.registration import UserRegistration
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.models.tcf_purpose_overrides import TCFPurposeOverride
from fides.api.oauth.roles import VIEWER
from fides.config import CONFIG
from fides.connectors.fides.fides_client import FidesClient

logging.getLogger("faker").setLevel(logging.ERROR)
# disable verbose faker logging
faker = Faker()
integration_config = load_toml("tests/fixtures/integration_test_config.toml")

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
def allow_custom_privacy_request_field_collection_enabled():
    original_value = CONFIG.execution.allow_custom_privacy_request_field_collection
    CONFIG.execution.allow_custom_privacy_request_field_collection = True
    yield
    CONFIG.execution.allow_custom_privacy_request_field_collection = original_value


@pytest.fixture(scope="function")
def allow_custom_privacy_request_field_collection_disabled():
    original_value = CONFIG.execution.allow_custom_privacy_request_field_collection
    CONFIG.execution.allow_custom_privacy_request_field_collection = False
    yield
    CONFIG.execution.allow_custom_privacy_request_field_collection = original_value


@pytest.fixture(scope="function")
def allow_custom_privacy_request_fields_in_request_execution_enabled():
    original_value = (
        CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution
    )
    CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution = True
    yield
    CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution = (
        original_value
    )


@pytest.fixture(scope="function")
def allow_custom_privacy_request_fields_in_request_execution_disabled():
    original_value = (
        CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution
    )
    CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution = False
    yield
    CONFIG.execution.allow_custom_privacy_request_fields_in_request_execution = (
        original_value
    )


@pytest.fixture(scope="function")
def set_max_privacy_request_download_rows():
    original_value = CONFIG.admin_ui.max_privacy_request_download_rows
    CONFIG.admin_ui.max_privacy_request_download_rows = 1
    yield
    CONFIG.admin_ui.max_privacy_request_download_rows = original_value


@pytest.fixture(scope="function")
def subject_request_download_ui_enabled():
    original_value = CONFIG.security.subject_request_download_ui_enabled
    CONFIG.security.subject_request_download_ui_enabled = True
    yield
    CONFIG.security.subject_request_download_ui_enabled = original_value


@pytest.fixture(scope="function")
def dsr_testing_tools_enabled():
    original_value = CONFIG.security.dsr_testing_tools_enabled
    CONFIG.security.dsr_testing_tools_enabled = True
    yield
    CONFIG.security.dsr_testing_tools_enabled = original_value


@pytest.fixture(scope="function")
def dsr_testing_tools_disabled():
    original_value = CONFIG.security.dsr_testing_tools_enabled
    CONFIG.security.dsr_testing_tools_enabled = False
    yield
    CONFIG.security.dsr_testing_tools_enabled = original_value


@pytest.fixture(scope="function")
def system_with_no_uses(db: Session) -> Generator[System, None, None]:
    system = System.create(
        db=db,
        data={
            "fides_key": "system_fides_key",
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
            "name": "TCF System Test",
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
            "name": "Test AC System",
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
            "name": "Test AC System 2",
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
            "name": "Test AC System 3",
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
            "name": "Test AC System 4",
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
            "name": "Captify",
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
            "name": "Emerse",
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
            "name": "Skimbit (Skimlinks, Taboola)",
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
def enable_erasure_request_finalization_required(db):
    """Enable erasure finalization via config"""
    original_value = CONFIG.execution.erasure_request_finalization_required
    CONFIG.execution.erasure_request_finalization_required = True
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.erasure_request_finalization_required = original_value
    ApplicationConfig.update_config_set(db, CONFIG)


@pytest.fixture(scope="function")
def disable_erasure_request_finalization_required(db):
    """Disable erasure finalization via config"""
    original_value = CONFIG.execution.erasure_request_finalization_required
    CONFIG.execution.erasure_request_finalization_required = False
    ApplicationConfig.update_config_set(db, CONFIG)
    yield
    CONFIG.execution.erasure_request_finalization_required = original_value
    ApplicationConfig.update_config_set(db, CONFIG)
