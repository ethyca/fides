from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import ConnectionException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.connection_configuration.connection_secrets_mongodb import (
    MongoDBSchema,
)
from fides.api.service.connectors.mongodb_connector import MongoDBConnector


@pytest.mark.unit
class TestMongoDBConnector:
    """Unit tests for MongoDBConnector build_uri and SSL configuration logic"""

    def test_build_uri_srv_connection_no_port(
        self, mongo_connection_config: ConnectionConfig, db: Session
    ):
        """Test that SRV connections don't include port in host part"""
        mongo_connection_config.secrets = {
            "host": "cluster.example.com",
            "username": "mongo_user",
            "password": "mongo_pass",
            "defaultauthdb": "mongo_test",
            "use_srv": True,  # This should trigger line 48
            "port": 27017,  # Port should be ignored for SRV
        }
        mongo_connection_config.save(db)

        connector = MongoDBConnector(configuration=mongo_connection_config)
        uri = connector.build_uri()

        # Should use mongodb+srv scheme and not include port
        assert uri.startswith("mongodb+srv://")
        assert "cluster.example.com" in uri
        assert ":27017" not in uri  # Port should not be in the URI for SRV

    def test_build_uri_standard_connection_with_port(
        self, mongo_connection_config: ConnectionConfig, db: Session
    ):
        """Test that standard connections include port in host part"""

        mongo_connection_config.secrets = {
            "host": "localhost",
            "username": "mongo_user",
            "password": "mongo_pass",
            "defaultauthdb": "mongo_test",
            "use_srv": False,
            "port": 27017,
        }
        mongo_connection_config.save(db)

        connector = MongoDBConnector(configuration=mongo_connection_config)
        uri = connector.build_uri()

        # Should use standard mongodb scheme and include port
        assert uri.startswith("mongodb://")
        assert "localhost:27017" in uri

    def test_build_uri_ssl_enabled_explicitly(
        self, mongo_connection_config: ConnectionConfig, db: Session
    ):
        """Test SSL enabled case"""

        mongo_connection_config.secrets = {
            "host": "localhost",
            "username": "mongo_user",
            "password": "mongo_pass",
            "defaultauthdb": "mongo_test",
            "use_srv": False,
            "ssl_enabled": True,
        }
        mongo_connection_config.save(db)

        connector = MongoDBConnector(configuration=mongo_connection_config)
        uri = connector.build_uri()

        assert "ssl=true" in uri

    def test_build_uri_ssl_disabled_with_srv(
        self, mongo_connection_config: ConnectionConfig, db: Session
    ):
        """Test SSL disabled for SRV connection (line 66)"""
        mongo_connection_config.secrets = {
            "host": "cluster.example.com",
            "username": "mongo_user",
            "password": "mongo_pass",
            "defaultauthdb": "mongo_test",
            "use_srv": True,  # SRV connection
            "ssl_enabled": False,
        }
        mongo_connection_config.save(db)

        connector = MongoDBConnector(configuration=mongo_connection_config)
        uri = connector.build_uri()

        assert "ssl=false" in uri

    def test_determine_ssl_enabled_explicit_setting(
        self, mongo_connection_config: ConnectionConfig
    ):
        """Test that explicit SSL setting takes precedence"""

        connector = MongoDBConnector(configuration=mongo_connection_config)

        # Test explicit True
        config = MongoDBSchema(
            host="localhost",
            username="user",
            password="pass",
            defaultauthdb="test",
            ssl_enabled=True,
            use_srv=False,
        )
        assert connector._determine_ssl_enabled(config) is True

        # Test explicit False
        config = MongoDBSchema(
            host="localhost",
            username="user",
            password="pass",
            defaultauthdb="test",
            ssl_enabled=False,
            use_srv=True,  # SRV would default to True, but explicit False should take precedence
        )
        assert connector._determine_ssl_enabled(config) is False

    def test_determine_ssl_enabled_srv_default(
        self, mongo_connection_config: ConnectionConfig
    ):
        """Test that SRV connections default to SSL enabled"""

        connector = MongoDBConnector(configuration=mongo_connection_config)

        config = MongoDBSchema(
            host="cluster.example.com",
            username="user",
            password="pass",
            defaultauthdb="test",
            ssl_enabled=None,  # No explicit setting
            use_srv=True,  # This should trigger line 80
        )
        assert connector._determine_ssl_enabled(config) is True

    def test_determine_ssl_enabled_standard_default(
        self, mongo_connection_config: ConnectionConfig
    ):
        """Test that standard connections default to SSL disabled"""

        connector = MongoDBConnector(configuration=mongo_connection_config)

        config = MongoDBSchema(
            host="localhost",
            username="user",
            password="pass",
            defaultauthdb="test",
            ssl_enabled=None,  # No explicit setting
            use_srv=False,  # Standard connection should default to SSL disabled
        )
        assert connector._determine_ssl_enabled(config) is False

    @patch("fides.api.service.connectors.mongodb_connector.MongoClient")
    def test_create_client_value_error_exception(
        self, mock_mongo_client, mongo_connection_config: ConnectionConfig
    ):
        """Test ValueError exception handling in create_client"""
        # Configure the mock to raise a ValueError
        mock_mongo_client.side_effect = ValueError("Invalid URI format")

        connector = MongoDBConnector(configuration=mongo_connection_config)

        with pytest.raises(ConnectionException) as exc_info:
            connector.create_client()

        assert "Value Error connecting to MongoDB: Invalid URI format" in str(
            exc_info.value
        )

    @patch("fides.api.service.connectors.mongodb_connector.MongoClient")
    def test_create_client_generic_exception(
        self, mock_mongo_client, mongo_connection_config: ConnectionConfig
    ):
        """Test generic Exception handling in create_client (lines 118-119)"""
        # Configure the mock to raise a generic exception
        mock_mongo_client.side_effect = RuntimeError("Connection failed")

        connector = MongoDBConnector(configuration=mongo_connection_config)

        with pytest.raises(ConnectionException) as exc_info:
            connector.create_client()

        assert "Error connecting to MongoDB: Connection failed" in str(exc_info.value)

    def test_build_uri_ssl_combinations(
        self, mongo_connection_config: ConnectionConfig, db: Session
    ):
        """Test various SSL configuration combinations to ensure proper URI generation"""
        connector = MongoDBConnector(configuration=mongo_connection_config)

        # Test 1: Standard connection, SSL enabled
        mongo_connection_config.secrets = {
            "host": "localhost",
            "username": "user",
            "password": "pass",
            "defaultauthdb": "test",
            "use_srv": False,
            "ssl_enabled": True,
        }
        mongo_connection_config.save(db)
        uri = connector.build_uri()
        assert "mongodb://" in uri
        assert "ssl=true" in uri

        # Test 2: SRV connection, SSL enabled (default)
        mongo_connection_config.secrets = {
            "host": "cluster.example.com",
            "username": "user",
            "password": "pass",
            "defaultauthdb": "test",
            "use_srv": True,
            "ssl_enabled": None,  # Should default to True for SRV
        }
        mongo_connection_config.save(db)
        uri = connector.build_uri()
        assert "mongodb+srv://" in uri
        assert "ssl=true" in uri  # Should be added because SRV defaults to SSL enabled

        # Test 3: SRV connection, SSL explicitly disabled
        mongo_connection_config.secrets = {
            "host": "cluster.example.com",
            "username": "user",
            "password": "pass",
            "defaultauthdb": "test",
            "use_srv": True,
            "ssl_enabled": False,  # Explicitly disabled
        }
        mongo_connection_config.save(db)
        uri = connector.build_uri()
        assert "mongodb+srv://" in uri
        assert "ssl=false" in uri  # Should be added to override SRV default
