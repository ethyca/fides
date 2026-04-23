from unittest.mock import MagicMock, patch

import pytest
from requests import Request

from fides.api.common_exceptions import FidesopsException, NoSuchStrategyException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.authentication.authentication_strategy_aws_iam_role import (
    AWSIAMRoleAuthenticationStrategy,
)

STRATEGY_CONFIG = {"aws_service": "execute-api", "region_name": "us-east-1"}


@pytest.fixture
def secret_keys_secrets():
    return {
        "auth_method": "secret_keys",
        "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    }


@pytest.fixture
def automatic_secrets():
    return {"auth_method": "automatic"}


@pytest.fixture
def assume_role_secrets(secret_keys_secrets):
    return {**secret_keys_secrets, "aws_assume_role_arn": "arn:aws:iam::123456789012:role/MyRole"}


@pytest.fixture
def connection_config_secret_keys(secret_keys_secrets):
    return ConnectionConfig(key="aws_test_connector", secrets=secret_keys_secrets)


@pytest.fixture
def connection_config_automatic(automatic_secrets):
    return ConnectionConfig(key="aws_auto_connector", secrets=automatic_secrets)


@pytest.fixture
def connection_config_assume_role(assume_role_secrets):
    return ConnectionConfig(key="aws_assume_role_connector", secrets=assume_role_secrets)


@pytest.fixture
def connection_config_no_secrets():
    return ConnectionConfig(key="aws_no_secrets_connector", secrets=None)


@pytest.fixture
def prepared_request():
    return Request(method="GET", url="https://api.example.execute-api.us-east-1.amazonaws.com/prod/resource").prepare()


def _make_mock_session(security_token=None):
    """Build a mock boto3 session with fake resolved credentials."""
    creds = MagicMock()
    creds.access_key = "AKIAIOSFODNN7EXAMPLE"
    creds.secret_key = "wJalrXUtnFEMI"
    creds.token = security_token
    resolved = MagicMock()
    resolved.access_key = creds.access_key
    resolved.secret_key = creds.secret_key
    resolved.token = security_token
    session = MagicMock()
    session.get_credentials.return_value.resolve.return_value = resolved
    return session, resolved


class TestAWSIAMRoleStrategyRegistration:
    def test_strategy_registered_via_get_strategy(self):
        strategy = AuthenticationStrategy.get_strategy("aws_iam_role", STRATEGY_CONFIG)
        assert isinstance(strategy, AWSIAMRoleAuthenticationStrategy)

    def test_strategy_stores_config(self):
        strategy = AuthenticationStrategy.get_strategy("aws_iam_role", STRATEGY_CONFIG)
        assert strategy.aws_service == "execute-api"
        assert strategy.region_name == "us-east-1"

    def test_invalid_strategy_raises(self):
        with pytest.raises(NoSuchStrategyException):
            AuthenticationStrategy.get_strategy("nonexistent_strategy", {})

    def test_missing_aws_service_raises(self):
        with pytest.raises(Exception):
            AuthenticationStrategy.get_strategy("aws_iam_role", {"region_name": "us-east-1"})

    def test_missing_region_name_raises(self):
        with pytest.raises(Exception):
            AuthenticationStrategy.get_strategy("aws_iam_role", {"aws_service": "execute-api"})


class TestAWSIAMRoleAddAuthentication:
    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.botocore.auth.SigV4Auth")
    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.get_aws_session")
    def test_secret_keys_signs_request(self, mock_get_session, mock_sigv4, connection_config_secret_keys, prepared_request):
        session, resolved_creds = _make_mock_session()
        mock_get_session.return_value = session

        mock_signer = MagicMock()
        mock_sigv4.return_value = mock_signer

        def apply_headers(aws_req):
            aws_req.headers["Authorization"] = "AWS4-HMAC-SHA256 Credential=..."
            aws_req.headers["X-Amz-Date"] = "20240101T000000Z"

        mock_signer.add_auth.side_effect = apply_headers

        strategy = AWSIAMRoleAuthenticationStrategy(
            configuration=MagicMock(aws_service="execute-api", region_name="us-east-1")
        )
        result = strategy.add_authentication(prepared_request, connection_config_secret_keys)

        mock_get_session.assert_called_once_with(
            auth_method="secret_keys",
            storage_secrets=connection_config_secret_keys.secrets,
            assume_role_arn=None,
        )
        mock_sigv4.assert_called_once_with(resolved_creds, "execute-api", "us-east-1")
        mock_signer.add_auth.assert_called_once()
        assert "Authorization" in result.headers
        assert "X-Amz-Date" in result.headers

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.botocore.auth.SigV4Auth")
    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.get_aws_session")
    def test_automatic_mode_signs_request(self, mock_get_session, mock_sigv4, connection_config_automatic, prepared_request):
        session, resolved_creds = _make_mock_session()
        mock_get_session.return_value = session
        mock_signer = MagicMock()
        mock_sigv4.return_value = mock_signer
        mock_signer.add_auth.side_effect = lambda r: r.headers.update({"Authorization": "AWS4...", "X-Amz-Date": "20240101T000000Z"})

        strategy = AWSIAMRoleAuthenticationStrategy(
            configuration=MagicMock(aws_service="execute-api", region_name="us-east-1")
        )
        result = strategy.add_authentication(prepared_request, connection_config_automatic)

        mock_get_session.assert_called_once_with(
            auth_method="automatic",
            storage_secrets=connection_config_automatic.secrets,
            assume_role_arn=None,
        )
        assert "Authorization" in result.headers

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.botocore.auth.SigV4Auth")
    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.get_aws_session")
    def test_assume_role_passes_arn(self, mock_get_session, mock_sigv4, connection_config_assume_role, prepared_request):
        session, resolved_creds = _make_mock_session(security_token="TOKEN123")
        mock_get_session.return_value = session
        mock_signer = MagicMock()
        mock_sigv4.return_value = mock_signer
        mock_signer.add_auth.side_effect = lambda r: r.headers.update({
            "Authorization": "AWS4...",
            "X-Amz-Date": "20240101T000000Z",
            "X-Amz-Security-Token": "TOKEN123",
        })

        strategy = AWSIAMRoleAuthenticationStrategy(
            configuration=MagicMock(aws_service="execute-api", region_name="us-east-1")
        )
        result = strategy.add_authentication(prepared_request, connection_config_assume_role)

        mock_get_session.assert_called_once_with(
            auth_method="secret_keys",
            storage_secrets=connection_config_assume_role.secrets,
            assume_role_arn="arn:aws:iam::123456789012:role/MyRole",
        )
        assert "X-Amz-Security-Token" in result.headers

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.botocore.auth.SigV4Auth")
    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.get_aws_session")
    def test_no_secrets_defaults_to_automatic(self, mock_get_session, mock_sigv4, connection_config_no_secrets, prepared_request):
        session, _ = _make_mock_session()
        mock_get_session.return_value = session
        mock_sigv4.return_value = MagicMock()

        strategy = AWSIAMRoleAuthenticationStrategy(
            configuration=MagicMock(aws_service="execute-api", region_name="us-east-1")
        )
        strategy.add_authentication(prepared_request, connection_config_no_secrets)

        mock_get_session.assert_called_once_with(
            auth_method="automatic",
            storage_secrets={},
            assume_role_arn=None,
        )

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.get_aws_session")
    def test_session_error_raises_fides_exception(self, mock_get_session, connection_config_secret_keys, prepared_request):
        mock_get_session.side_effect = ValueError("Invalid credentials")

        strategy = AWSIAMRoleAuthenticationStrategy(
            configuration=MagicMock(aws_service="execute-api", region_name="us-east-1")
        )
        with pytest.raises(FidesopsException, match="Failed to obtain AWS session"):
            strategy.add_authentication(prepared_request, connection_config_secret_keys)

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.botocore.auth.SigV4Auth")
    @patch("fides.api.service.authentication.authentication_strategy_aws_iam_role.get_aws_session")
    def test_original_headers_preserved(self, mock_get_session, mock_sigv4, connection_config_automatic, prepared_request):
        """Existing headers on the request are not removed by signing."""
        prepared_request.headers["X-Custom-Header"] = "my-value"
        session, _ = _make_mock_session()
        mock_get_session.return_value = session
        mock_signer = MagicMock()
        mock_sigv4.return_value = mock_signer
        mock_signer.add_auth.side_effect = lambda r: r.headers.update({"Authorization": "AWS4...", "X-Amz-Date": "20240101T000000Z"})

        strategy = AWSIAMRoleAuthenticationStrategy(
            configuration=MagicMock(aws_service="execute-api", region_name="us-east-1")
        )
        result = strategy.add_authentication(prepared_request, connection_config_automatic)

        assert result.headers.get("X-Custom-Header") == "my-value"
        assert "Authorization" in result.headers
