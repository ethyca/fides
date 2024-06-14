from typing import Any, Dict, List, Optional

from loguru import logger

from fides.api.common_exceptions import ConnectionException
from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import ConnectionTestStatus
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_s3 import S3Schema
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.query_config import QueryConfig
from fides.api.util.aws_util import get_aws_session
from fides.api.util.collection_util import Row


class S3Connector(BaseConnector):
    """
    AWS S3 Connector - this is currently used just to test connections to S3.

    NOTE: No DSR processing is yet supported for S3.
    """

    def create_client(self) -> Any:  # type: ignore
        """Returns a client for s3"""
        config = S3Schema(**self.configuration.secrets or {})
        return get_aws_session(
            auth_method=config.auth_method.value,
            storage_secrets=config.dict(),  # type: ignore
            assume_role_arn=config.aws_assume_role_arn,
        )

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """DSR execution not yet supported for S3"""
        raise NotImplementedError()

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Connects to AWS S3 and gets caller identity to validate credentials.
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
        """DSR execution not yet supported for S3"""

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """DSR execution not yet supported for S3"""

    def close(self) -> None:
        """Close any held resources"""
        # no held resources for S3 connector
