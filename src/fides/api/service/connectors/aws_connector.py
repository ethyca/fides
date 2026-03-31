"""AWS Cloud Infrastructure connector.

Used for cloud infra discovery: validates credentials via sts:GetCallerIdentity.
DSR traversal is not supported.
"""

from typing import Any, Dict, List, NoReturn, Optional

from loguru import logger

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_aws import AWSSchema
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.util.aws_util import get_aws_session
from fides.api.util.collection_util import Row


class AWSConnector(BaseConnector):
    """AWS Cloud Infrastructure connector for credential validation."""

    @property
    def dsr_supported(self) -> bool:
        return False

    def create_client(self) -> Any:
        """Returns a boto3 session for AWS."""
        config = AWSSchema(**self.configuration.secrets or {})
        return get_aws_session(
            auth_method=config.auth_method.value,
            storage_secrets=config.model_dump(mode="json"),  # type: ignore
            assume_role_arn=config.aws_assume_role_arn,
        )

    def query_config(self, node: ExecutionNode) -> NoReturn:
        """Query config not implemented for AWS connector."""
        raise NotImplementedError("Query config not implemented for AWS connector")

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Validate AWS credentials via sts:GetCallerIdentity.

        Returns:
            ConnectionTestStatus.succeeded if credentials are valid.
        """
        logger.info("Starting test connection to {}", self.configuration.key)
        try:
            session = self.client()
            sts_client = session.client("sts")
            sts_client.get_caller_identity()
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
        """DSR data retrieval is not supported for AWS connector."""
        return []

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
        input_data: Optional[Dict[str, List[Any]]] = None,
    ) -> int:
        """DSR data masking is not supported for AWS connector."""
        return 0

    def close(self) -> None:
        """Release any held resources. No-op for AWS connector."""
