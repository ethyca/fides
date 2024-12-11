from datetime import datetime, timedelta
from typing import Generator
from unittest import mock
from unittest.mock import Mock

import pytest
from requests import PreparedRequest, Request
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException, OAuth2TokenException
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.authentication.authentication_strategy_oauth2_client_credentials import (
    OAuth2ClientCredentialsAuthenticationStrategy,
)


class TestAddAuthentication:
    # happy path, being able to use the existing access token
    def test_oauth2_authentication(
        self,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        # set a future expiration date for the access token
        oauth2_client_credentials_connection_config.secrets["expires_at"] = (
            datetime.utcnow() + timedelta(days=1)
        ).timestamp()

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_client_credentials", oauth2_client_credentials_configuration
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_client_credentials_connection_config
        )
        assert (
            authenticated_request.headers["Authorization"]
            == f"Bearer {oauth2_client_credentials_connection_config.secrets['access_token']}"
        )

    @mock.patch(
        "fides.api.service.authentication.authentication_strategy_oauth2_base.OAuth2AuthenticationStrategyBase.get_access_token"
    )
    def test_oauth2_authentication_missing_access_token(
        self,
        mock_access_token: Mock,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        access_token = "new_access"
        mock_access_token.return_value = access_token

        # remove the access_token
        oauth2_client_credentials_connection_config.secrets["access_token"] = None

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy: OAuth2ClientCredentialsAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_client_credentials", oauth2_client_credentials_configuration
            )
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_client_credentials_connection_config
        )
        assert (
            authenticated_request.headers["Authorization"] == f"Bearer {access_token}"
        )

    @mock.patch(
        "fides.api.service.authentication.authentication_strategy_oauth2_base.OAuth2AuthenticationStrategyBase.get_access_token"
    )
    def test_oauth2_authentication_empty_access_token(
        self,
        mock_access_token: Mock,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        access_token = "new_access"
        mock_access_token.return_value = access_token

        # replace the access_token with an empty string
        oauth2_client_credentials_connection_config.secrets["access_token"] = ""

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_client_credentials", oauth2_client_credentials_configuration
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_client_credentials_connection_config
        )
        assert (
            authenticated_request.headers["Authorization"] == f"Bearer {access_token}"
        )

    def test_oauth2_authentication_missing_secrets(
        self,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        # mix of missing and empty secrets
        oauth2_client_credentials_connection_config.secrets["access_token"] = None
        oauth2_client_credentials_connection_config.secrets["client_id"] = None
        oauth2_client_credentials_connection_config.secrets["client_secret"] = ""

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy: OAuth2ClientCredentialsAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_client_credentials", oauth2_client_credentials_configuration
            )
        )
        with pytest.raises(FidesopsException) as exc:
            auth_strategy.add_authentication(
                req, oauth2_client_credentials_connection_config
            )
        assert (
            str(exc.value)
            == f"Missing required secret(s) 'client_id, client_secret' for oauth2_client_credentials_connector"
        )

    # access token expired, call refresh request
    @mock.patch("fides.api.models.connectionconfig.ConnectionConfig.update")
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_oauth2_authentication_successful_refresh(
        self,
        mock_send: Mock,
        mock_connection_config_update: Mock,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        # mock the json response from calling the token refresh request
        mock_send().json.return_value = {"access_token": "new_access"}

        # expire the access token
        oauth2_client_credentials_connection_config.secrets["expires_at"] = 0

        # the request we want to authenticate
        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_client_credentials", oauth2_client_credentials_configuration
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_client_credentials_connection_config
        )
        assert authenticated_request.headers["Authorization"] == "Bearer new_access"

        # verify correct values for connection_config update
        mock_connection_config_update.assert_called_once_with(
            mock.ANY,
            data={
                "secrets": {
                    "domain": "localhost",
                    "client_id": "client",
                    "client_secret": "secret",
                    "access_token": "new_access",
                    "expires_at": 0,
                }
            },
        )

    # no refresh request defined, should still add access token
    def test_oauth2_authentication_no_refresh(
        self,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        oauth2_client_credentials_configuration["refresh_request"] = None

        # the request we want to authenticate
        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_client_credentials", oauth2_client_credentials_configuration
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_client_credentials_connection_config
        )
        assert (
            authenticated_request.headers["Authorization"]
            == f"Bearer {oauth2_client_credentials_connection_config.secrets['access_token']}"
        )

    # access token expired, unable to refresh
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_oauth2_authentication_failed_refresh(
        self,
        mock_send: Mock,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        # mock the json response from calling the token refresh request
        mock_send().json.return_value = {"error": "invalid_request"}

        # expire the access token
        oauth2_client_credentials_connection_config.secrets["expires_at"] = 0

        # the request we want to authenticate
        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_client_credentials", oauth2_client_credentials_configuration
        )
        with pytest.raises(OAuth2TokenException) as exc:
            auth_strategy.add_authentication(
                req, oauth2_client_credentials_connection_config
            )
        assert (
            str(exc.value)
            == f"Unable to retrieve token for {oauth2_client_credentials_connection_config.key} (invalid_request)."
        )


class TestAccessTokenRequest:
    @mock.patch("datetime.datetime")
    @mock.patch("fides.api.models.connectionconfig.ConnectionConfig.update")
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_get_access_token(
        self,
        mock_send: Mock,
        mock_connection_config_update: Mock,
        mock_time: Mock,
        db: Session,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        # cast some time magic
        mock_time.utcnow.return_value = datetime(2022, 5, 22)

        # mock the json response from calling the access token request
        expires_in = 7200
        mock_send().json.return_value = {
            "access_token": "new_access",
            "expires_in": expires_in,
        }

        auth_strategy: OAuth2ClientCredentialsAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_client_credentials", oauth2_client_credentials_configuration
            )
        )
        auth_strategy.get_access_token(oauth2_client_credentials_connection_config, db)

        # verify correct values for connection_config update
        mock_connection_config_update.assert_called_once_with(
            mock.ANY,
            data={
                "secrets": {
                    "domain": "localhost",
                    "client_id": "client",
                    "client_secret": "secret",
                    "access_token": "new_access",
                    "expires_at": int(datetime.utcnow().timestamp()) + expires_in,
                }
            },
        )

    @mock.patch("datetime.datetime")
    @mock.patch("fides.api.models.connectionconfig.ConnectionConfig.update")
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_get_access_token_no_expires_in(
        self,
        mock_send: Mock,
        mock_connection_config_update: Mock,
        mock_time: Mock,
        db: Session,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        """
        Make sure we can use the expires_in value in the config if no expires_in
        is provided in the access token response.
        """

        # set a fixed time
        mock_time.utcnow.return_value = datetime(2022, 5, 22)

        # mock the json response from calling the access token request
        mock_send().json.return_value = {
            "access_token": "new_access",
        }

        oauth2_client_credentials_configuration["expires_in"] = 3600
        auth_strategy: OAuth2ClientCredentialsAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_client_credentials", oauth2_client_credentials_configuration
            )
        )
        auth_strategy.get_access_token(oauth2_client_credentials_connection_config, db)

        # verify correct values for connection_config update
        mock_connection_config_update.assert_called_once_with(
            mock.ANY,
            data={
                "secrets": {
                    "domain": "localhost",
                    "client_id": "client",
                    "client_secret": "secret",
                    "access_token": "new_access",
                    "expires_at": int(datetime.utcnow().timestamp())
                    + oauth2_client_credentials_configuration["expires_in"],
                }
            },
        )

    def test_get_access_token_missing_secrets(
        self,
        db: Session,
        oauth2_client_credentials_connection_config,
        oauth2_client_credentials_configuration,
    ):
        # erase some secrets
        oauth2_client_credentials_connection_config.secrets["client_id"] = None
        oauth2_client_credentials_connection_config.secrets["client_secret"] = ""

        auth_strategy: OAuth2ClientCredentialsAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_client_credentials", oauth2_client_credentials_configuration
            )
        )
        with pytest.raises(FidesopsException) as exc:
            auth_strategy.get_access_token(
                oauth2_client_credentials_connection_config, db
            )
        assert (
            str(exc.value)
            == f"Missing required secret(s) 'client_id, client_secret' for oauth2_client_credentials_connector"
        )
