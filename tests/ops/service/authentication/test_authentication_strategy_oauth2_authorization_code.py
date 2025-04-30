from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import Mock

import pytest
from requests import PreparedRequest, Request
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException, OAuth2TokenException
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.authentication.authentication_strategy_oauth2_authorization_code import (
    OAuth2AuthorizationCodeAuthenticationStrategy,
)


class TestAddAuthentication:
    # happy path, being able to use the existing access token
    def test_oauth2_authentication(
        self,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # set a future expiration date for the access token
        oauth2_authorization_code_connection_config.secrets["expires_at"] = (
            datetime.utcnow() + timedelta(days=1)
        ).timestamp()

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_authorization_code_connection_config
        )
        assert (
            authenticated_request.headers["Authorization"]
            == f"Bearer {oauth2_authorization_code_connection_config.secrets['access_token']}"
        )

    def test_oauth2_authentication_missing_access_token(
        self,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # remove the access_token
        oauth2_authorization_code_connection_config.secrets["access_token"] = None

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_authorization_code", oauth2_authorization_code_configuration
        )
        with pytest.raises(FidesopsException) as exc:
            auth_strategy.add_authentication(
                req, oauth2_authorization_code_connection_config
            )
        assert str(exc.value) == (
            f"OAuth2 access token not found for {oauth2_authorization_code_connection_config.key}, please "
            f"authenticate connection via /api/v1/connection/{oauth2_authorization_code_connection_config.key}/authorize"
        )

    def test_oauth2_authentication_empty_access_token(
        self,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # replace the access_token with an empty string
        oauth2_authorization_code_connection_config.secrets["access_token"] = ""

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_authorization_code", oauth2_authorization_code_configuration
        )
        with pytest.raises(FidesopsException) as exc:
            auth_strategy.add_authentication(
                req, oauth2_authorization_code_connection_config
            )
        assert str(exc.value) == (
            f"OAuth2 access token not found for {oauth2_authorization_code_connection_config.key}, please "
            f"authenticate connection via /api/v1/connection/{oauth2_authorization_code_connection_config.key}/authorize"
        )

    def test_oauth2_authentication_missing_secrets(
        self,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # mix of missing and empty secrets
        oauth2_authorization_code_connection_config.secrets["client_id"] = None
        oauth2_authorization_code_connection_config.secrets["client_secret"] = ""

        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_authorization_code", oauth2_authorization_code_configuration
        )
        with pytest.raises(FidesopsException) as exc:
            auth_strategy.add_authentication(
                req, oauth2_authorization_code_connection_config
            )
        assert (
            str(exc.value)
            == f"Missing required secret(s) 'client_id, client_secret' for oauth2_authorization_code_connector"
        )

    # access token expired, call refresh request
    @mock.patch("fides.api.models.connectionconfig.ConnectionConfig.update")
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_oauth2_authentication_successful_refresh(
        self,
        mock_send: Mock,
        mock_connection_config_update: Mock,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # mock the json response from calling the token refresh request
        mock_send().json.return_value = {"access_token": "new_access"}

        # expire the access token
        oauth2_authorization_code_connection_config.secrets["expires_at"] = 0

        # the request we want to authenticate
        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_authorization_code", oauth2_authorization_code_configuration
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_authorization_code_connection_config
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
                    "redirect_uri": "https://localhost/callback",
                    "access_token": "new_access",
                    "refresh_token": "refresh",
                    "expires_at": 0,
                }
            },
        )

    # no refresh request defined, should still add access token
    def test_oauth2_authentication_no_refresh(
        self,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        oauth2_authorization_code_configuration["refresh_request"] = None

        # the request we want to authenticate
        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_authorization_code", oauth2_authorization_code_configuration
        )
        authenticated_request = auth_strategy.add_authentication(
            req, oauth2_authorization_code_connection_config
        )
        assert (
            authenticated_request.headers["Authorization"]
            == f"Bearer {oauth2_authorization_code_connection_config.secrets['access_token']}"
        )

    # access token expired, unable to refresh
    @mock.patch("fides.api.service.connectors.saas_connector.AuthenticatedClient.send")
    def test_oauth2_authentication_failed_refresh(
        self,
        mock_send: Mock,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # mock the json response from calling the token refresh request
        mock_send().json.return_value = {"error": "invalid_request"}

        # expire the access token
        oauth2_authorization_code_connection_config.secrets["expires_at"] = 0

        # the request we want to authenticate
        req: PreparedRequest = Request(method="POST", url="https://localhost").prepare()

        auth_strategy = AuthenticationStrategy.get_strategy(
            "oauth2_authorization_code", oauth2_authorization_code_configuration
        )
        with pytest.raises(OAuth2TokenException) as exc:
            auth_strategy.add_authentication(
                req, oauth2_authorization_code_connection_config
            )
        assert (
            str(exc.value)
            == f"Unable to retrieve token for {oauth2_authorization_code_connection_config.key} (invalid_request)."
        )


class TestAuthorizationUrl:
    @mock.patch(
        "fides.api.service.authentication.authentication_strategy_oauth2_authorization_code.OAuth2AuthorizationCodeAuthenticationStrategy._generate_state"
    )
    @mock.patch(
        "fides.api.models.authentication_request.AuthenticationRequest.create_or_update"
    )
    def test_get_authorization_url(
        self,
        mock_create_or_update: Mock,
        mock_state: Mock,
        db: Session,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        state = "unique_value"
        mock_state.return_value = state
        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        assert (
            auth_strategy.get_authorization_url(
                db, oauth2_authorization_code_connection_config
            )
            == "https://localhost/auth/authorize?client_id=client&redirect_uri=https%3A%2F%2Flocalhost%2Fcallback&response_type=code&scope=admin.read+admin.write&state=unique_value"
        )
        mock_create_or_update.assert_called_once_with(
            mock.ANY,
            data={
                "connection_key": oauth2_authorization_code_connection_config.key,
                "state": state,
                "referer": None,
            },
        )

    def test_get_authorization_url_missing_secrets(
        self,
        db: Session,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # erase some secrets
        oauth2_authorization_code_connection_config.secrets["client_id"] = None
        oauth2_authorization_code_connection_config.secrets["client_secret"] = ""

        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        with pytest.raises(FidesopsException) as exc:
            auth_strategy.get_authorization_url(
                db, oauth2_authorization_code_connection_config
            )
        assert (
            str(exc.value)
            == f"Missing required secret(s) 'client_id, client_secret' for oauth2_authorization_code_connector"
        )

    @mock.patch(
        "fides.api.service.authentication.authentication_strategy_oauth2_authorization_code.OAuth2AuthorizationCodeAuthenticationStrategy._generate_state"
    )
    @mock.patch(
        "fides.api.models.authentication_request.AuthenticationRequest.create_or_update"
    )
    def test_get_authorization_url_with_referer(
        self,
        mock_create_or_update: Mock,
        mock_state: Mock,
        db: Session,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        state = "unique_value"
        referer = "http://test.com"
        mock_state.return_value = state
        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        assert (
            auth_strategy.get_authorization_url(
                db, oauth2_authorization_code_connection_config, referer
            )
            == "https://localhost/auth/authorize?client_id=client&redirect_uri=https%3A%2F%2Flocalhost%2Fcallback&response_type=code&scope=admin.read+admin.write&state=unique_value"
        )
        mock_create_or_update.assert_called_once_with(
            mock.ANY,
            data={
                "connection_key": oauth2_authorization_code_connection_config.key,
                "state": state,
                "referer": referer,
            },
        )

    @mock.patch(
        "fides.api.service.authentication.authentication_strategy_oauth2_authorization_code.OAuth2AuthorizationCodeAuthenticationStrategy._generate_state"
    )
    @mock.patch(
        "fides.api.models.authentication_request.AuthenticationRequest.create_or_update"
    )
    def test_get_authorization_url_without_referer(
        self,
        mock_create_or_update: Mock,
        mock_state: Mock,
        db: Session,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        state = "unique_value"
        mock_state.return_value = state
        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        assert (
            auth_strategy.get_authorization_url(
                db, oauth2_authorization_code_connection_config
            )
            == "https://localhost/auth/authorize?client_id=client&redirect_uri=https%3A%2F%2Flocalhost%2Fcallback&response_type=code&scope=admin.read+admin.write&state=unique_value"
        )
        mock_create_or_update.assert_called_once_with(
            mock.ANY,
            data={
                "connection_key": oauth2_authorization_code_connection_config.key,
                "state": state,
                "referer": None,
            },
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
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # cast some time magic
        mock_time.utcnow.return_value = datetime(2022, 5, 22)

        # mock the json response from calling the access token request
        expires_in = 7200
        mock_send().json.return_value = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "expires_in": expires_in,
        }

        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        oauth2_authorization_code_connection_config.secrets = {
            **oauth2_authorization_code_connection_config.secrets,
            "code": "auth_code",
        }
        auth_strategy.get_access_token(oauth2_authorization_code_connection_config)

        # verify correct values for connection_config update
        mock_connection_config_update.assert_called_once_with(
            mock.ANY,
            data={
                "secrets": {
                    "domain": "localhost",
                    "client_id": "client",
                    "client_secret": "secret",
                    "redirect_uri": "https://localhost/callback",
                    "access_token": "new_access",
                    "refresh_token": "new_refresh",
                    "code": "auth_code",
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
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
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
            "refresh_token": "new_refresh",
        }

        oauth2_authorization_code_configuration["expires_in"] = 3600
        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        oauth2_authorization_code_connection_config.secrets = {
            **oauth2_authorization_code_connection_config.secrets,
            "code": "auth_code",
        }
        auth_strategy.get_access_token(oauth2_authorization_code_connection_config, db)

        # verify correct values for connection_config update
        mock_connection_config_update.assert_called_once_with(
            mock.ANY,
            data={
                "secrets": {
                    "domain": "localhost",
                    "client_id": "client",
                    "client_secret": "secret",
                    "redirect_uri": "https://localhost/callback",
                    "access_token": "new_access",
                    "refresh_token": "new_refresh",
                    "code": "auth_code",
                    "expires_at": int(datetime.utcnow().timestamp())
                    + oauth2_authorization_code_configuration["expires_in"],
                }
            },
        )

    def test_get_access_token_missing_secrets(
        self,
        db: Session,
        oauth2_authorization_code_connection_config,
        oauth2_authorization_code_configuration,
    ):
        # erase some secrets
        oauth2_authorization_code_connection_config.secrets["client_id"] = None
        oauth2_authorization_code_connection_config.secrets["client_secret"] = ""

        auth_strategy: OAuth2AuthorizationCodeAuthenticationStrategy = (
            AuthenticationStrategy.get_strategy(
                "oauth2_authorization_code", oauth2_authorization_code_configuration
            )
        )
        with pytest.raises(FidesopsException) as exc:
            oauth2_authorization_code_connection_config.secrets = {
                **oauth2_authorization_code_connection_config.secrets,
                "code": "auth_code",
            }
            auth_strategy.get_access_token(oauth2_authorization_code_connection_config)
        assert (
            str(exc.value)
            == f"Missing required secret(s) 'client_id, client_secret' for oauth2_authorization_code_connector"
        )
