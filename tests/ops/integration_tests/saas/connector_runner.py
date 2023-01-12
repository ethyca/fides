import random
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.policy import Policy
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.core.config import get_config
from fides.lib.cryptography import cryptographic_util

CONFIG = get_config()


class ConnectorRunner:
    """
    A util class responsible for creating the entities required for
    testing connectivity and access/erasure requests for a SaaS connector
    """

    def __init__(self, db, secrets, connector_type: str):
        self.db = db
        self.connection_config = _connection_config(
            db, _config(connector_type), secrets
        )
        self.dataset_config = _dataset_config(
            db, self.connection_config, _dataset(connector_type)
        )

    def test_connection(self):
        """Connection test using the connectors test_request"""
        get_connector(self.connection_config).test_connection()

    async def access_request(
        self,
        access_policy: Policy,
        identities: Dict[str, Any],
    ) -> Dict[str, List[Row]]:
        """Access request for a given access policy and identities"""
        fides_key = self.connection_config.key
        privacy_request = PrivacyRequest(
            id=f"test_{fides_key}_access_request_{random.randint(0, 1000)}"
        )
        identity = Identity(**identities)
        privacy_request.cache_identity(identity)

        merged_graph = self.dataset_config.get_graph()
        graph = DatasetGraph(merged_graph)

        return await graph_task.run_access_request(
            privacy_request,
            access_policy,
            graph,
            [self.connection_config],
            identities,
            self.db,
        )

    async def strict_erasure_request(
        self,
        access_policy: Policy,
        erasure_policy: Policy,
        identities: Dict[str, Any],
    ) -> Dict[str, int]:
        """
        Erasure request with masking_strict set to true,
        meaning we will only update data, not delete it
        """

        # store the existing masking_strict value so we can reset it at the end of the test
        masking_strict = CONFIG.execution.masking_strict
        CONFIG.execution.masking_strict = True

        fides_key = self.connection_config.key
        privacy_request = PrivacyRequest(
            id=f"test_{fides_key}_access_request_{random.randint(0, 1000)}"
        )
        identity = Identity(**identities)
        privacy_request.cache_identity(identity)

        merged_graph = self.dataset_config.get_graph()
        graph = DatasetGraph(merged_graph)

        await graph_task.run_access_request(
            privacy_request,
            access_policy,
            graph,
            [self.connection_config],
            identities,
            self.db,
        )

        erasure_results = await graph_task.run_erasure(
            privacy_request,
            erasure_policy,
            graph,
            [self.connection_config],
            identities,
            get_cached_data_for_erasures(privacy_request.id),
            self.db,
        )

        # reset masking_strict value
        CONFIG.execution.masking_strict = masking_strict
        return erasure_results

    async def non_strict_erasure_request(
        self,
        access_policy: Policy,
        erasure_policy: Policy,
        identities: Dict[str, Any],
    ) -> Dict[str, int]:
        """
        Erasure request with masking_strict set to false,
        meaning we will use deletes to mask data if an update
        is not available
        """

        # store the existing masking_strict value so we can reset it at the end of the test
        masking_strict = CONFIG.execution.masking_strict
        CONFIG.execution.masking_strict = False

        fides_key = self.connection_config.key
        privacy_request = PrivacyRequest(
            id=f"test_{fides_key}_access_request_{random.randint(0, 1000)}"
        )
        identity = Identity(**identities)
        privacy_request.cache_identity(identity)

        merged_graph = self.dataset_config.get_graph()
        graph = DatasetGraph(merged_graph)

        await graph_task.run_access_request(
            privacy_request,
            access_policy,
            graph,
            [self.connection_config],
            identities,
            self.db,
        )

        erasure_results = await graph_task.run_erasure(
            privacy_request,
            erasure_policy,
            graph,
            [self.connection_config],
            identities,
            get_cached_data_for_erasures(privacy_request.id),
            self.db,
        )

        # reset masking_strict value
        CONFIG.execution.masking_strict = masking_strict
        return erasure_results


def _config(connector_type: str) -> Dict[str, Any]:
    return load_config_with_replacement(
        f"data/saas/config/{connector_type}_config.yml",
        "<instance_fides_key>",
        f"{connector_type}_instance",
    )


def _dataset(connector_type: str) -> Dict[str, Any]:
    return load_dataset_with_replacement(
        f"data/saas/dataset/{connector_type}_dataset.yml",
        "<instance_fides_key>",
        f"{connector_type}_instance",
    )[0]


def _connection_config(db: Session, config, secrets) -> ConnectionConfig:
    fides_key = config["fides_key"]
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.saas,
            "access": AccessLevel.write,
            "secrets": secrets,
            "saas_config": config,
        },
    )
    return connection_config


def _dataset_config(
    db: Session,
    connection_config: ConnectionConfig,
    dataset: Dict[str, Any],
) -> DatasetConfig:
    fides_key = dataset["fides_key"]
    connection_config.name = fides_key
    connection_config.key = fides_key
    connection_config.save(db=db)
    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "dataset": dataset,
        },
    )
    return dataset


def generate_random_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"
