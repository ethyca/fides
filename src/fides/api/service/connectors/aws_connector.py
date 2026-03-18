"""Connector for AWS Cloud Infrastructure connection type."""

from typing import Any, Dict, List, Optional

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_aws import AWSSchema
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_configs.query_config import QueryConfig
from fides.api.util.aws_util import get_aws_session
from fides.api.util.collection_util import Row
from loguru import logger


class AWSConnector(BaseConnector):
    """Connector for AWS Cloud Infrastructure.

    Used solely for credential validation — data retrieval is handled by
    the infra monitor service, not the DSR traversal engine.
    """

    def create_client(self) -> Any:
        """Return a boto3 Session using the configured AWS credentials."""
        config = AWSSchema(**self.configuration.secrets or {})
        return get_aws_session(
            auth_method=config.auth_method.value,
            storage_secrets=config.model_dump(mode="json"),
            assume_role_arn=config.aws_assume_role_arn,
        )

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """DSR execution not supported for AWS Cloud Infrastructure."""
        raise NotImplementedError(
            "DSR traversal is not supported for AWS Cloud Infrastructure connections."
        )

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """Validate AWS credentials by calling sts:GetCallerIdentity."""
        logger.info("Starting test connection to {}", self.configuration.key)
        try:
            session = self.client()
            session.client("sts").get_caller_identity()
        except Exception as error:
            raise ConnectionException(str(error))
        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """DSR retrieval not supported."""
        raise NotImplementedError(
            "DSR retrieval is not supported for AWS Cloud Infrastructure connections."
        )

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> int:
        """DSR masking not supported."""
        raise NotImplementedError(
            "DSR masking is not supported for AWS Cloud Infrastructure connections."
        )

    def close(self) -> None:
        """No persistent connection to close."""
