from unittest.mock import MagicMock, patch

import pytest
from google.cloud.sql.connector import Connector
from google.oauth2.service_account import Credentials
from sqlalchemy.engine import Engine

from fides.api.schemas.connection_configuration.enums import (
    google_cloud_sql_ip_type as ip_type,
)
from fides.api.service.connectors.google_cloud_mysql_connector import (
    GoogleCloudSQLMySQLConnector,
)


@pytest.fixture
def mock_config():
    return {
        "db_iam_user": "test-user",
        "instance_connection_name": "project:region:instance",
        "dbname": "test-db",
        "keyfile_creds": {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": (
                "-----BEGIN PRIVATE KEY-----\n"
                "MIIE...sample...key\n"
                "-----END PRIVATE KEY-----\n"
            ),
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": (
                "https://www.googleapis.com/oauth2/v1/certs"
            ),
            "client_x509_cert_url": (
                "https://www.googleapis.com/robot/v1/metadata/x509/"
                "test.iam.gserviceaccount.com"
            ),
            "universe_domain": "googleapis.com",
        },
        "ip_type": ip_type.GoogleCloudSQLIPType.private,
    }


@pytest.fixture
def connector(mock_config):
    connector = GoogleCloudSQLMySQLConnector(
        configuration=MagicMock(secrets=mock_config)
    )
    return connector


@patch(
    "fides.api.service.connectors.google_cloud_mysql_connector"
    ".service_account.Credentials",
    autospec=True,
)
@patch(
    "fides.api.service.connectors.google_cloud_mysql_connector" ".Connector",
    autospec=True,
)
@patch(
    "fides.api.service.connectors.google_cloud_mysql_connector" ".create_engine",
    autospec=True,
)
class TestGoogleCloudSQLMySQLConnectorCreateClient:
    """Tests for GoogleCloudSQLMySQLConnector.create_client method."""

    def test_success(
        self,
        mock_create_engine,
        mock_connector_class,
        mock_credentials_class,
        connector,
        mock_config,
    ):
        """Test successful creation of a database client."""
        mock_credentials = MagicMock(spec=Credentials)
        mock_credentials_class.from_service_account_info.return_value = mock_credentials
        mock_connector_instance = MagicMock(spec=Connector)
        mock_connector_class.return_value = mock_connector_instance
        mock_db_connection = MagicMock()
        mock_connector_instance.connect.return_value = mock_db_connection
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine

        result = connector.create_client()

        mock_credentials_class.from_service_account_info.assert_called_once_with(
            dict(mock_config["keyfile_creds"])
        )
        mock_connector_class.assert_called_once_with(credentials=mock_credentials)

        # Get the creator function that was passed to create_engine
        creator_fn = mock_create_engine.call_args[1]["creator"]
        # Call the creator function to verify it calls connect with right params
        creator_fn()
        mock_connector_instance.connect.assert_called_once_with(
            mock_config["instance_connection_name"],
            "pymysql",
            ip_type=mock_config["ip_type"],
            user=mock_config["db_iam_user"],
            db=mock_config["dbname"],
            enable_iam_auth=True,
        )

        mock_create_engine.assert_called_once()
        assert mock_create_engine.call_args[0][0] == "mysql+pymysql://"
        assert result == mock_engine

    def test_with_default_ip_type(
        self,
        mock_create_engine,
        mock_connector_class,
        mock_credentials_class,
        connector,
        mock_config,
    ):
        """Test client creation with default IP type."""
        # Remove ip_type from config
        connector.configuration.secrets["ip_type"] = None

        mock_credentials_class.from_service_account_info.return_value = MagicMock(
            spec=Credentials
        )
        mock_connector_instance = MagicMock(spec=Connector)
        mock_connector_class.return_value = mock_connector_instance
        mock_db_connection = MagicMock()
        mock_connector_instance.connect.return_value = mock_db_connection
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine

        result = connector.create_client()

        # Get and call the creator function
        creator_fn = mock_create_engine.call_args[1]["creator"]
        creator_fn()
        # Verify connect was called with default IP type
        mock_connector_instance.connect.assert_called_once_with(
            mock_config["instance_connection_name"],
            "pymysql",
            ip_type=ip_type.GoogleCloudSQLIPType.public,  # Default IP type
            user=mock_config["db_iam_user"],
            db=mock_config["dbname"],
            enable_iam_auth=True,
        )
        assert result == mock_engine
