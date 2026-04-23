from typing import Any, Dict

import botocore.auth
import botocore.awsrequest
from loguru import logger
from requests import PreparedRequest

from fides.api.common_exceptions import FidesopsException
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.saas.strategy_configuration import (
    AWSIAMRoleAuthenticationConfiguration,
    StrategyConfiguration,
)
from fides.api.schemas.storage.storage import AWSAuthMethod
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.util.aws_util import get_aws_session


class AWSIAMRoleAuthenticationStrategy(AuthenticationStrategy):
    """
    Signs outbound HTTP requests using AWS Signature Version 4 (SigV4).

    Credentials are sourced from connection_config.secrets using the same
    fields as BaseAWSSchema: auth_method, aws_access_key_id,
    aws_secret_access_key, and aws_assume_role_arn. Both 'secret_keys' and
    'automatic' (ambient IAM role) modes are supported, as is role assumption
    via aws_assume_role_arn.

    SaaS YAML example:
        authentication:
          strategy: aws_iam_role
          configuration:
            aws_service: execute-api
            region_name: us-east-1
    """

    name = "aws_iam_role"
    configuration_model = AWSIAMRoleAuthenticationConfiguration

    def __init__(self, configuration: AWSIAMRoleAuthenticationConfiguration) -> None:
        self.aws_service = configuration.aws_service
        self.region_name = configuration.region_name

    def add_authentication(
        self, request: PreparedRequest, connection_config: ConnectionConfig
    ) -> PreparedRequest:
        """Sign the request with AWS SigV4 using credentials from connection secrets."""
        secrets: Dict[str, Any] = connection_config.secrets or {}

        auth_method = secrets.get("auth_method", AWSAuthMethod.AUTOMATIC.value)

        logger.debug(
            "Signing request for {} with AWS IAM role strategy (auth_method={})",
            connection_config.key,
            auth_method,
        )

        try:
            session = get_aws_session(
                auth_method=auth_method,
                storage_secrets=secrets,  # type: ignore[arg-type]
                assume_role_arn=secrets.get("aws_assume_role_arn"),
            )
        except Exception as exc:
            raise FidesopsException(
                f"Failed to obtain AWS session for connector '{connection_config.key}': {exc}"
            ) from exc

        credentials = session.get_credentials().resolve()

        # Wrap in an AWSRequest so botocore's SigV4Auth can sign it.
        aws_req = botocore.awsrequest.AWSRequest(
            method=request.method,
            url=request.url,
            data=request.body,
            headers=dict(request.headers),
        )

        signer = botocore.auth.SigV4Auth(credentials, self.aws_service, self.region_name)
        signer.add_auth(aws_req)

        # Merge the signed headers (Authorization, X-Amz-Date, X-Amz-Security-Token, etc.)
        # back onto the original PreparedRequest.
        request.headers.update(dict(aws_req.headers))
        return request

    @staticmethod
    def get_configuration_model() -> StrategyConfiguration:
        return AWSIAMRoleAuthenticationConfiguration  # type: ignore[return-value]
