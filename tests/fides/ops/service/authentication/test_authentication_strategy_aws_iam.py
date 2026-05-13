from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from requests import Request

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.authentication.authentication_strategy_aws_iam import (
    TOKEN_REFRESH_BUFFER_SECONDS,
    AWSIAMAuthenticationStrategy,
)


@pytest.fixture
def static_key_secrets():
    return {
        "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "aws_region": "us-west-2",
    }


@pytest.fixture
def assume_role_secrets():
    return {
        "aws_assume_role_arn": "arn:aws:iam::123456789012:role/CustomerFidesRole",
        "aws_region": "us-east-1",
    }


@pytest.fixture
def static_key_connection_config(static_key_secrets):
    return ConnectionConfig(
        key="aws_iam_test_connector",
        secrets=static_key_secrets,
    )


@pytest.fixture
def assume_role_connection_config(assume_role_secrets):
    return ConnectionConfig(
        key="aws_iam_assume_role_connector",
        secrets=assume_role_secrets,
    )


class TestStrategyConfiguration:
    def test_strategy_registered(self):
        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        assert isinstance(strategy, AWSIAMAuthenticationStrategy)

    def test_default_service(self):
        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        assert strategy.service == "execute-api"

    def test_custom_service(self):
        strategy = AuthenticationStrategy.get_strategy(
            "aws_iam", {"service": "lambda"}
        )
        assert strategy.service == "lambda"

    def test_custom_region(self):
        strategy = AuthenticationStrategy.get_strategy(
            "aws_iam", {"region": "eu-west-1"}
        )
        assert strategy.aws_region == "eu-west-1"

    def test_default_region_is_none(self):
        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        assert strategy.aws_region is None


class TestCredentialResolution:
    def test_missing_secrets(self):
        connection_config = ConnectionConfig(key="test", secrets=None)
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/resource",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, connection_config)
        assert "Secrets are not configured" in str(exc.value)

    def test_missing_both_role_and_keys(self):
        connection_config = ConnectionConfig(
            key="test", secrets={"aws_region": "us-east-1"}
        )
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/resource",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, connection_config)
        assert "aws_assume_role_arn" in str(exc.value)

    def test_static_keys_sign_request(self, static_key_connection_config):
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-west-2.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(
            req, static_key_connection_config
        )

        assert "Authorization" in authenticated_request.headers
        assert "AWS4-HMAC-SHA256" in authenticated_request.headers["Authorization"]
        assert "X-Amz-Date" in authenticated_request.headers

    def test_static_keys_with_session_token(self):
        connection_config = ConnectionConfig(
            key="test",
            secrets={
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "aws_session_token": "FwoGZXIvYXdzEBYaDH...",
                "aws_region": "us-east-1",
            },
        )
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(req, connection_config)

        assert "X-Amz-Security-Token" in authenticated_request.headers


class TestAssumeRole:
    @patch("fides.api.service.authentication.authentication_strategy_aws_iam.boto3")
    def test_assume_role_signs_request(
        self, mock_boto3, assume_role_connection_config
    ):
        future_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIA_TEMP_KEY",
                "SecretAccessKey": "temp_secret",
                "SessionToken": "temp_session_token",
                "Expiration": future_expiry,
            }
        }
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sts
        mock_boto3.Session.return_value = mock_session

        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(
            req, assume_role_connection_config
        )

        assert "Authorization" in authenticated_request.headers
        assert "AWS4-HMAC-SHA256" in authenticated_request.headers["Authorization"]
        mock_sts.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/CustomerFidesRole",
            RoleSessionName="FidesSaaSConnectorSession",
        )

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam.boto3")
    def test_assume_role_with_base_credentials(self, mock_boto3):
        connection_config = ConnectionConfig(
            key="test",
            secrets={
                "aws_assume_role_arn": "arn:aws:iam::123456789012:role/SomeRole",
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "aws_region": "us-east-1",
            },
        )

        future_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIA_TEMP",
                "SecretAccessKey": "temp_secret",
                "SessionToken": "temp_token",
                "Expiration": future_expiry,
            }
        }
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sts
        mock_boto3.Session.return_value = mock_session

        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        strategy.add_authentication(req, connection_config)

        mock_boto3.Session.assert_called_once_with(
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            aws_session_token=None,
        )

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam.boto3")
    def test_assume_role_access_denied(self, mock_boto3, assume_role_connection_config):
        mock_sts = MagicMock()
        mock_sts.assume_role.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Not authorized"}},
            "AssumeRole",
        )
        mock_session = MagicMock()
        mock_session.client.return_value = mock_sts
        mock_boto3.Session.return_value = mock_session

        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, assume_role_connection_config)
        assert "Access denied" in str(exc.value)

    @patch("fides.api.service.authentication.authentication_strategy_aws_iam.boto3")
    def test_assume_role_no_credentials(
        self, mock_boto3, assume_role_connection_config
    ):
        mock_boto3.Session.side_effect = NoCredentialsError()

        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})

        with pytest.raises(FidesopsException) as exc:
            strategy.add_authentication(req, assume_role_connection_config)
        assert "No AWS credentials found" in str(exc.value)


class TestCredentialCaching:
    def test_uses_cached_credentials_when_valid(self, assume_role_secrets):
        future_expiry = int(
            (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
        )
        connection_config = ConnectionConfig(
            key="test",
            secrets={
                **assume_role_secrets,
                "aws_iam_access_key_id": "ASIA_CACHED",
                "aws_iam_secret_access_key": "cached_secret",
                "aws_iam_session_token": "cached_token",
                "aws_iam_credentials_expire_at": future_expiry,
            },
        )

        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(req, connection_config)

        assert "Authorization" in authenticated_request.headers
        assert "AWS4-HMAC-SHA256" in authenticated_request.headers["Authorization"]

    @patch(
        "fides.api.service.authentication.authentication_strategy_aws_iam.AWSIAMAuthenticationStrategy._refresh_assumed_role_credentials"
    )
    def test_refreshes_credentials_when_close_to_expiration(
        self, mock_refresh, assume_role_secrets
    ):
        from botocore.credentials import Credentials

        mock_refresh.return_value = Credentials(
            "ASIA_NEW", "new_secret", "new_token"
        )

        close_expiry = int(
            (
                datetime.now(timezone.utc)
                + timedelta(seconds=TOKEN_REFRESH_BUFFER_SECONDS - 60)
            ).timestamp()
        )
        connection_config = ConnectionConfig(
            key="test",
            secrets={
                **assume_role_secrets,
                "aws_iam_access_key_id": "ASIA_OLD",
                "aws_iam_secret_access_key": "old_secret",
                "aws_iam_session_token": "old_token",
                "aws_iam_credentials_expire_at": close_expiry,
            },
        )

        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        strategy.add_authentication(req, connection_config)

        mock_refresh.assert_called_once()


class TestRegionResolution:
    def test_region_from_configuration(self, static_key_secrets):
        connection_config = ConnectionConfig(
            key="test", secrets=static_key_secrets
        )
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-east-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "aws_iam", {"region": "ap-southeast-1"}
        )
        authenticated_request = strategy.add_authentication(req, connection_config)

        auth_header = authenticated_request.headers["Authorization"]
        assert "ap-southeast-1" in auth_header

    def test_region_from_secrets(self, static_key_secrets):
        connection_config = ConnectionConfig(
            key="test", secrets=static_key_secrets
        )
        req = Request(
            method="GET",
            url="https://custom-domain.example.com/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(req, connection_config)

        auth_header = authenticated_request.headers["Authorization"]
        assert "us-west-2" in auth_header

    def test_region_inferred_from_url(self):
        connection_config = ConnectionConfig(
            key="test",
            secrets={
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            },
        )
        req = Request(
            method="GET",
            url="https://abc123.execute-api.eu-central-1.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(req, connection_config)

        auth_header = authenticated_request.headers["Authorization"]
        assert "eu-central-1" in auth_header

    def test_region_falls_back_to_us_east_1(self):
        connection_config = ConnectionConfig(
            key="test",
            secrets={
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            },
        )
        req = Request(
            method="GET",
            url="https://custom-domain.example.com/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(req, connection_config)

        auth_header = authenticated_request.headers["Authorization"]
        assert "us-east-1" in auth_header


class TestRequestSigning:
    def test_preserves_existing_headers(self, static_key_connection_config):
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-west-2.amazonaws.com/prod/users",
            headers={"Content-Type": "application/json", "X-Custom": "value"},
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(
            req, static_key_connection_config
        )

        assert authenticated_request.headers["Content-Type"] == "application/json"
        assert authenticated_request.headers["X-Custom"] == "value"
        assert "Authorization" in authenticated_request.headers

    def test_signs_post_with_body(self, static_key_connection_config):
        req = Request(
            method="POST",
            url="https://abc123.execute-api.us-west-2.amazonaws.com/prod/users",
            json={"email": "test@example.com"},
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(
            req, static_key_connection_config
        )

        assert "Authorization" in authenticated_request.headers
        assert "AWS4-HMAC-SHA256" in authenticated_request.headers["Authorization"]

    def test_service_name_in_signature(self, static_key_connection_config):
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-west-2.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy("aws_iam", {})
        authenticated_request = strategy.add_authentication(
            req, static_key_connection_config
        )

        auth_header = authenticated_request.headers["Authorization"]
        assert "execute-api" in auth_header

    def test_custom_service_name(self, static_key_connection_config):
        req = Request(
            method="GET",
            url="https://abc123.execute-api.us-west-2.amazonaws.com/prod/users",
        ).prepare()

        strategy = AuthenticationStrategy.get_strategy(
            "aws_iam", {"service": "lambda"}
        )
        authenticated_request = strategy.add_authentication(
            req, static_key_connection_config
        )

        auth_header = authenticated_request.headers["Authorization"]
        assert "lambda" in auth_header
