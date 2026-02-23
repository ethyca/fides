import os
from pathlib import Path

import pytest

from fides.config import get_config
from tests.factories.base import BaseFactory

ROOT_PATH = Path().absolute()
CONFIG = get_config()
TEST_CONFIG_PATH = "tests/cli/test_config.toml"
TEST_INVALID_CONFIG_PATH = "tests/cli/test_invalid_config.toml"
TEST_DEPRECATED_CONFIG_PATH = "tests/cli/test_deprecated_config.toml"

pytest_plugins = [
    # Core infrastructure
    "tests.fixtures.db_fixtures",
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.user_role_fixtures",
    "tests.fixtures.celery_fixtures",
    "tests.fixtures.config_flag_fixtures",
    "tests.fixtures.test_data_fixtures",
    "tests.fixtures.gcs_fixtures",
    "tests.fixtures.system_fixtures",
    # Domain fixtures (split from application_fixtures.py)
    "tests.fixtures.storage_fixtures",
    "tests.fixtures.policy_fixtures",
    "tests.fixtures.webhook_fixtures",
    "tests.fixtures.privacy_request_fixtures",
    "tests.fixtures.privacy_notice_fixtures",
    "tests.fixtures.consent_fixtures",
    "tests.fixtures.experience_fixtures",
    "tests.fixtures.dataset_fixtures",
    "tests.fixtures.property_fixtures",
    "tests.fixtures.connection_fixtures",
    "tests.fixtures.attachment_fixtures",
    "tests.fixtures.application_fixtures",
    # Connector-specific fixtures
    "tests.fixtures.async_fixtures",
    "tests.fixtures.bigquery_fixtures",
    "tests.fixtures.datahub_fixtures",
    "tests.fixtures.detection_discovery_fixtures",
    "tests.fixtures.dynamodb_fixtures",
    "tests.fixtures.email_fixtures",
    "tests.fixtures.fides_connector_example_fixtures",
    "tests.fixtures.google_cloud_sql_mysql_fixtures",
    "tests.fixtures.google_cloud_sql_postgres_fixtures",
    "tests.fixtures.integration_fixtures",
    "tests.fixtures.manual_fixtures",
    "tests.fixtures.manual_webhook_fixtures",
    "tests.fixtures.mariadb_fixtures",
    "tests.fixtures.messaging_fixtures",
    "tests.fixtures.mongodb_fixtures",
    "tests.fixtures.mssql_fixtures",
    "tests.fixtures.mysql_fixtures",
    "tests.fixtures.okta_fixtures",
    "tests.fixtures.postgres_fixtures",
    "tests.fixtures.rds_mysql_fixtures",
    "tests.fixtures.rds_postgres_fixtures",
    "tests.fixtures.redshift_fixtures",
    "tests.fixtures.saas",
    "tests.fixtures.saas_erasure_order_fixtures",
    "tests.fixtures.saas_example_fixtures",
    "tests.fixtures.scylladb_fixtures",
    "tests.fixtures.snowflake_fixtures",
    "tests.fixtures.timescale_fixtures",
]


@pytest.fixture(autouse=True)
def _set_factory_session(db):
    """Inject the test DB session into factory_boy factories."""
    BaseFactory._meta.sqlalchemy_session = db


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node):
    """Pytest hook automatically called for each xdist worker node configuration."""
    if hasattr(node, "workerinput") and node.workerinput:
        worker_id = node.workerinput["workerid"]
        print(
            f"[Configure Node] Configuring database and config for worker {worker_id}..."
        )

        os.environ["FIDES__DATABASE__TEST_DB"] = f"fides_test_{worker_id}"

        get_config.cache_clear()
        fides_config = get_config()
        sync_db_uri = fides_config.database.sqlalchemy_test_database_uri
        async_db_uri = fides_config.database.async_database_uri

        print(
            f"[Configure Node] Sync DB URI: {sync_db_uri} Async DB URI: {async_db_uri}"
        )
    else:
        print(
            "[Configure Node] Skipping DB setup/config update on single node or non-xdist run."
        )
