from datetime import datetime, timedelta, timezone
from typing import Any, Dict, NoReturn, Optional
from urllib.parse import urlparse

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from botocore.exceptions import ClientError, NoCredentialsError
from loguru import logger
from requests import PreparedRequest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import (
    AWSIAMAuthenticationConfiguration,
    StrategyConfiguration,
)
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.logger import Pii

TOKEN_REFRESH_BUFFER_SECONDS = 300


class AWSIAMAuthenticationStrategy(AuthenticationStrategy):
    """
    Authenticates HTTP requests using AWS IAM (Signature V4).

    Supports two modes:
    - AssumeRole: Customer provides an IAM Role ARN. Fides assumes the role
      via STS to get temporary credentials, then signs requests with SigV4.
    - Static keys: Customer provides AWS access key ID and secret access key
      directly.

    Designed for authenticating against AWS API Gateway endpoints protected
    by IAM authorization.
    """

    name = "aws_iam"
    configuration_model = AWSIAMAuthenticationConfiguration

    def __init__(self, configuration: AWSIAMAuthenticationConfiguration):
        self.aws_region = configuration.region
        self.service = configuration.service

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        credentials = self._get_credentials(connection_config)
        region = self._resolve_region(request.url, connection_config)

        aws_request = AWSRequest(
            method=request.method,
            url=request.url,
            headers=dict(request.headers) if request.headers else {},
            data=request.body or "",
        )

        SigV4Auth(credentials, self.service, region).add_auth(aws_request)

        request.headers.update(dict(aws_request.headers))
        return request

    def _get_credentials(self, connection_config: ConnectionConfig) -> Credentials:
        secrets = connection_config.secrets
        if not secrets:
            raise FidesopsException(
                "Secrets are not configured for this connector. "
                "AWS IAM authentication requires either an assume_role_arn "
                "or aws_access_key_id and aws_secret_access_key."
            )

        assume_role_arn = secrets.get("aws_assume_role_arn")
        if assume_role_arn:
            return self._get_assumed_role_credentials(secrets, connection_config)

        access_key_id = secrets.get("aws_access_key_id")
        secret_access_key = secrets.get("aws_secret_access_key")
        if not access_key_id or not secret_access_key:
            raise FidesopsException(
                "AWS IAM authentication requires either 'aws_assume_role_arn' "
                "or both 'aws_access_key_id' and 'aws_secret_access_key'."
            )
        session_token = secrets.get("aws_session_token")
        return Credentials(access_key_id, secret_access_key, session_token)

    def _get_assumed_role_credentials(
        self,
        secrets: Dict[str, Any],
        connection_config: ConnectionConfig,
    ) -> Credentials:
        cached_key = secrets.get("aws_iam_access_key_id")
        cached_secret = secrets.get("aws_iam_secret_access_key")
        cached_token = secrets.get("aws_iam_session_token")
        cached_expiry = secrets.get("aws_iam_credentials_expire_at")

        if cached_key and cached_secret and cached_token and cached_expiry:
            if not self._is_close_to_expiration(cached_expiry):
                return Credentials(cached_key, cached_secret, cached_token)

        return self._refresh_assumed_role_credentials(secrets, connection_config)

    def _refresh_assumed_role_credentials(
        self,
        secrets: Dict[str, Any],
        connection_config: ConnectionConfig,
    ) -> Credentials:
        import boto3

        assume_role_arn = secrets["aws_assume_role_arn"]

        logger.info(
            "Assuming AWS IAM role for {}",
            connection_config.key,
        )

        try:
            access_key_id = secrets.get("aws_access_key_id")
            secret_access_key = secrets.get("aws_secret_access_key")

            if access_key_id and secret_access_key:
                session = boto3.Session(
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key,
                    aws_session_token=secrets.get("aws_session_token"),
                )
            else:
                session = boto3.Session()

            sts_client = session.client("sts")
            response = sts_client.assume_role(
                RoleArn=assume_role_arn,
                RoleSessionName="FidesSaaSConnectorSession",
            )

            temp_creds = response["Credentials"]
            access_key = temp_creds["AccessKeyId"]
            secret_key = temp_creds["SecretAccessKey"]
            session_token = temp_creds["SessionToken"]
            expiration = temp_creds["Expiration"]

            expires_at = int(expiration.timestamp())
            self._store_credentials(
                connection_config, access_key, secret_key, session_token, expires_at
            )

            logger.info(
                "Successfully assumed AWS IAM role for {}",
                connection_config.key,
            )

            return Credentials(access_key, secret_key, session_token)

        except (ClientError, NoCredentialsError) as exc:
            self._handle_credential_error(exc, connection_config)

    def _resolve_region(
        self, url: Optional[str], connection_config: ConnectionConfig
    ) -> str:
        if self.aws_region:
            return self.aws_region

        secrets = connection_config.secrets or {}
        region_from_secrets = secrets.get("aws_region")
        if region_from_secrets:
            return region_from_secrets

        if url:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            parts = hostname.split(".")
            if len(parts) >= 4 and parts[-2] == "amazonaws" and parts[-1] == "com":
                return parts[-3]

        return "us-east-1"

    def _is_close_to_expiration(self, expires_at: int) -> bool:
        buffer_time = datetime.now(timezone.utc) + timedelta(
            seconds=TOKEN_REFRESH_BUFFER_SECONDS
        )
        return expires_at < buffer_time.timestamp()

    def _store_credentials(
        self,
        connection_config: ConnectionConfig,
        access_key_id: str,
        secret_access_key: str,
        session_token: str,
        expires_at: int,
    ) -> None:
        db: Optional[Session] = Session.object_session(connection_config)
        if db is None:
            logger.warning(
                "Unable to cache AWS IAM credentials for {} - no database session available",
                connection_config.key,
            )
            return

        updated_secrets = {
            **(connection_config.secrets or {}),
            "aws_iam_access_key_id": access_key_id,
            "aws_iam_secret_access_key": secret_access_key,
            "aws_iam_session_token": session_token,
            "aws_iam_credentials_expire_at": expires_at,
        }
        connection_config.update(db, data={"secrets": updated_secrets})
        logger.debug(
            "Cached AWS IAM credentials for {} (expires at {})",
            connection_config.key,
            datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        )

    def _handle_credential_error(
        self, exc: Exception, connection_config: ConnectionConfig
    ) -> NoReturn:
        error_msg = str(exc)
        logger.error(
            "Error assuming AWS IAM role for {}: {}",
            connection_config.key,
            Pii(error_msg),
        )

        if isinstance(exc, NoCredentialsError):
            user_message = (
                "No AWS credentials found. Provide either aws_access_key_id "
                "and aws_secret_access_key, or ensure the Fides environment "
                "has AWS credentials configured (e.g. via instance profile)."
            )
        elif isinstance(exc, ClientError):
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                user_message = (
                    "Access denied when assuming the IAM role. Verify that "
                    "the role's trust policy allows Fides to assume it and "
                    "that the provided credentials have sts:AssumeRole permission."
                )
            elif error_code in ("MalformedPolicyDocument", "PackedPolicyTooLarge"):
                user_message = f"IAM role configuration error: {error_code}. Check the role ARN and trust policy."
            else:
                user_message = f"AWS STS error ({error_code}): {error_msg}"
        else:
            user_message = f"Failed to assume AWS IAM role: {error_msg}"

        raise FidesopsException(user_message) from exc

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return AWSIAMAuthenticationConfiguration  # type: ignore
