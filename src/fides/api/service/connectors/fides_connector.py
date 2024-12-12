from typing import Any, Dict, List, Optional, Set

from loguru import logger as log

from fides.api.graph.execution import ExecutionNode
from fides.api.models.connectionconfig import (
    ConnectionConfig,
    ConnectionTestStatus,
    ConnectionType,
)
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest, RequestTask
from fides.api.schemas.connection_configuration.connection_secrets_fides import (
    FidesConnectorSchema,
)
from fides.api.schemas.policy import ActionType
from fides.api.schemas.redis_cache import Identity
from fides.api.service.connectors.base_connector import BaseConnector
from fides.api.service.connectors.fides.fides_client import FidesClient
from fides.api.service.connectors.query_config import QueryConfig
from fides.api.util.collection_util import Row
from fides.api.util.errors import FidesError

DEFAULT_POLLING_TIMEOUT: int = 1800
DEFAULT_POLLING_INTERVAL: int = 30


class FidesConnector(BaseConnector[FidesClient]):
    """A connector that forwards requests to other Fides instances

    This has not been updated to work with DSR 3.0 and is assumed to break.
    """

    def __init__(self, configuration: ConnectionConfig):
        super().__init__(configuration)
        config = FidesConnectorSchema(**self.configuration.secrets or {})
        self.polling_timeout = (
            config.polling_timeout
            if config.polling_timeout
            else DEFAULT_POLLING_TIMEOUT
        )
        self.polling_interval = (
            config.polling_interval
            if config.polling_interval
            else DEFAULT_POLLING_INTERVAL
        )

    def query_config(self, node: ExecutionNode) -> QueryConfig[Any]:
        """Return the query config that corresponds to this connector type"""
        # no query config for fides connectors
        raise NotImplementedError()

    def create_client(self) -> FidesClient:
        """Returns a client used to connect to a Fides instance"""
        config = FidesConnectorSchema(**self.configuration.secrets or {})

        # use polling_timeout here to provide a base read timeout
        # on the HTTP client underlying the FidesClient, since even
        # in non-polling context, we may hit a blocking HTTP call
        # e.g., in privacy request creation we can block until completion
        client = FidesClient(
            uri=config.uri,
            username=config.username,
            password=config.password,
            connection_read_timeout=self.polling_timeout,
        )

        client.login()
        return client

    def test_connection(self) -> Optional[ConnectionTestStatus]:
        """
        Tests connection to the configured Fides server with configured credentials
        by attempting an authorized API call and ensuring success
        """
        log.info("Starting test connection to {}", self.configuration.key)
        try:
            client: FidesClient = self.client()
            client.request_status()
        except Exception as e:
            log.error("Error testing connection to remote Fides {}", str(e))
            return ConnectionTestStatus.failed

        log.info("Successful connection test for {}", self.configuration.key)
        return ConnectionTestStatus.succeeded

    def retrieve_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        input_data: Dict[str, List[Any]],
    ) -> List[Row]:
        """Execute access request and fetch access data from remote Fides"""
        identity_data = {
            **privacy_request.get_persisted_identity().labeled_dict(),
            **privacy_request.get_cached_identity_data(),
        }
        if not identity_data:
            raise FidesError(
                f"No identity data found for privacy request {privacy_request.id}, cannot execute Fides connector!"
            )
        log.info(
            f"{self.configuration.key} starting retrieve_data for privacy request {privacy_request.id}..."
        )

        client: FidesClient = self.client()

        # initiate privacy request execution on child
        pr_id: str = client.create_privacy_request(
            external_id=privacy_request.external_id or privacy_request.id,
            identity=Identity(**identity_data),
            policy_key=policy.key,
        )

        # block till privacy request completes on child
        client.poll_for_request_completion(
            privacy_request_id=pr_id,
            timeout=self.polling_timeout or None,
            interval=self.polling_interval or None,
        )

        # for each rule, get appropriate results from the child
        # store in a dict keyed by rule.key, to be unpacked later by request framework
        results: Dict[str, Dict[str, List[Row]]] = {
            rule.key: client.retrieve_request_results(
                privacy_request_id=pr_id, rule_key=rule.key
            )
            for rule in policy.get_rules_for_action(action_type=ActionType.access)
        }

        log.info(
            f"{self.configuration.key} finished retrieve_data for privacy request {privacy_request.id}"
        )
        return [results]

    def mask_data(
        self,
        node: ExecutionNode,
        policy: Policy,
        privacy_request: PrivacyRequest,
        request_task: RequestTask,
        rows: List[Row],
    ) -> int:
        """Execute an erasure request on remote fides"""
        identity_data = {
            **privacy_request.get_persisted_identity().labeled_dict(),
            **privacy_request.get_cached_identity_data(),
        }
        if not identity_data:
            raise FidesError(
                f"No identity data found for privacy request {privacy_request.id}, cannot execute Fides connector!"
            )
        log.info(
            f"{self.configuration.key} starting mask_data for privacy request {privacy_request.id}..."
        )

        client: FidesClient = self.client()
        update_ct = 0
        for _ in rows:
            pr_id = client.create_privacy_request(
                external_id=privacy_request.external_id,
                identity=Identity(**identity_data),
                policy_key=policy.key,
            )
            client.poll_for_request_completion(
                privacy_request_id=pr_id,
                timeout=self.polling_timeout,
                interval=self.polling_interval,
            )
            update_ct += 1

        log.info(
            f"{self.configuration.key} finished mask_data for privacy request {privacy_request.id}"
        )
        return update_ct

    def close(self) -> None:
        """Close any held resources"""
        # no held resources for Fides client


def filter_fides_connector_datasets(
    connector_configs: List[ConnectionConfig],
) -> Set[str]:
    """
    Helper function to retrieve the `fides_key`s of any `Dataset`s associated
    with any Fides connectors in the provided `List` of `ConnectionConfig`s.

    Returns a `Set` of `str`s containing the `fides_key`
    of the `Dataset`
    """
    return {
        dataset.fides_key
        for connector_config in connector_configs
        for dataset in connector_config.datasets
        if connector_config.connection_type == ConnectionType.fides
    }
