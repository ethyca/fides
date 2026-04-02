"""Tests for AWS Cloud Infrastructure connector."""

from unittest.mock import MagicMock, patch

import pytest

from fides.api.common_exceptions import ConnectionException
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.service.connectors.aws_connector import AWSConnector


@pytest.fixture
def aws_connection_config(db):
    """Create a ConnectionConfig with AWS type and secret_keys auth."""
    config = ConnectionConfig(
        key="test_aws_connection",
        name="Test AWS Connection",
        connection_type=ConnectionType.aws,
        access="read",
        secrets={
            "auth_method": "secret_keys",
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_assume_role_arn": "arn:aws:iam::123456789012:role/MyRole",
        },
    )
    config.save(db)
    yield config


class TestAWSConnector:
    def test_create_client(self, aws_connection_config):
        """create_client passes secrets and auth_method to get_aws_session."""
        connector = AWSConnector(aws_connection_config)
        mock_session = MagicMock()
        with patch(
            "fides.api.service.connectors.aws_connector.get_aws_session",
            return_value=mock_session,
        ) as mock_get_session:
            result = connector.create_client()
        kwargs = mock_get_session.call_args.kwargs
        assert kwargs["auth_method"] == "secret_keys"
        assert kwargs["storage_secrets"]["aws_access_key_id"] == "AKIAIOSFODNN7EXAMPLE"
        assert kwargs["assume_role_arn"] == "arn:aws:iam::123456789012:role/MyRole"
        assert result is mock_session

    def test_test_connection_success(self, aws_connection_config):
        """test_connection returns succeeded when sts:GetCallerIdentity succeeds."""
        connector = AWSConnector(aws_connection_config)
        mock_session = MagicMock()
        mock_sts = MagicMock()
        mock_session.client.return_value = mock_sts
        with patch.object(connector, "client", return_value=mock_session):
            result = connector.test_connection()
        mock_session.client.assert_called_once_with("sts")
        mock_sts.get_caller_identity.assert_called_once()
        assert result == ConnectionTestStatus.succeeded

    def test_test_connection_failure(self, aws_connection_config):
        """test_connection raises ConnectionException when sts call fails."""
        connector = AWSConnector(aws_connection_config)
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock(
            get_caller_identity=MagicMock(side_effect=Exception("Invalid credentials"))
        )
        with patch.object(connector, "client", return_value=mock_session):
            with pytest.raises(ConnectionException, match="Invalid credentials"):
                connector.test_connection()

    def test_dsr_supported_false(self, aws_connection_config):
        connector = AWSConnector(aws_connection_config)
        assert connector.dsr_supported is False

    def test_retrieve_data_returns_empty(self, aws_connection_config):
        """retrieve_data is a no-op since DSR is not supported."""
        connector = AWSConnector(aws_connection_config)
        assert (
            connector.retrieve_data(
                MagicMock(), MagicMock(), MagicMock(), MagicMock(), {}
            )
            == []
        )

    def test_mask_data_returns_zero(self, aws_connection_config):
        """mask_data is a no-op since DSR is not supported."""
        connector = AWSConnector(aws_connection_config)
        assert (
            connector.mask_data(MagicMock(), MagicMock(), MagicMock(), MagicMock(), [])
            == 0
        )

    def test_query_config_raises(self, aws_connection_config):
        """query_config raises NotImplementedError."""
        connector = AWSConnector(aws_connection_config)
        with pytest.raises(NotImplementedError):
            connector.query_config(MagicMock())
