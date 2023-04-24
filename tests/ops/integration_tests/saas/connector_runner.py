import random
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from fides.api.ctl.sql_models import Dataset as CtlDataset
from fides.api.ops.cryptography import cryptographic_util
from fides.api.ops.graph.config import GraphDataset
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
from fides.api.ops.util.cache import FidesopsRedis
from fides.api.ops.util.collection_util import Row
from fides.api.ops.util.saas_util import (
    load_config_with_replacement,
    load_dataset_with_replacement,
)
from fides.core.config import get_config

CONFIG = get_config()


class ConnectorRunner:
    """
    A util class responsible for creating the entities required for
    testing connectivity and access/erasure requests for a SaaS connector
    """

    def __init__(
        self,
        db,
        cache: FidesopsRedis,
        connector_type: str,
        secrets: Dict[str, Any],
        external_references: Optional[Dict[str, Any]] = None,
        erasure_external_references: Optional[Dict[str, Any]] = None,
    ):
        self.db = db
        self.cache = cache
        self.connector_type = connector_type
        self.external_references = external_references
        self.erasure_external_references = erasure_external_references

        # load the config and dataset from the yaml files
        self.config = _config(connector_type)
        self.dataset = _dataset(connector_type)

        # update secrets with external reference dataset
        for external_reference in self.config.get("external_references", []):
            external_reference_name = external_reference["name"]
            secrets[external_reference_name] = {
                "dataset": f"{connector_type}_external_dataset",
                "field": f"{connector_type}_external_collection.{external_reference_name}",
                "direction": "from",
            }

        # create and save the connection config and dataset config to the database
        self.connection_config = _connection_config(db, self.config, secrets)
        self.dataset_config = _dataset_config(db, self.connection_config, self.dataset)

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

        # cache external dataset data
        if self.external_references:
            self.cache.set_encoded_object(
                f"{privacy_request.id}__access_request__{self.connector_type}_external_dataset:{self.connector_type}_external_collection",
                [self.external_references],
            )

        graph_list = [self.dataset_config.get_graph()]
        connection_config_list = [self.connection_config]
        _process_external_references(self.db, graph_list, connection_config_list)
        dataset_graph = DatasetGraph(*graph_list)

        access_results = await graph_task.run_access_request(
            privacy_request,
            access_policy,
            dataset_graph,
            connection_config_list,
            identities,
            self.db,
        )
        # verify we returned at least one row for each collection in the dataset
        for collection in self.dataset["collections"]:
            assert len(access_results[f"{fides_key}:{collection['name']}"])
        return access_results

    async def strict_erasure_request(
        self,
        access_policy: Policy,
        erasure_policy: Policy,
        identities: Dict[str, Any],
    ) -> Tuple[Dict, Dict]:
        """
        Erasure request with masking_strict set to true,
        meaning we will only update data, not delete it
        """

        # store the existing masking_strict value so we can reset it at the end of the test
        masking_strict = CONFIG.execution.masking_strict
        CONFIG.execution.masking_strict = True

        access_results, erasure_results = await self._base_erasure_request(
            access_policy, erasure_policy, identities
        )

        # reset masking_strict value
        CONFIG.execution.masking_strict = masking_strict
        return access_results, erasure_results

    async def non_strict_erasure_request(
        self,
        access_policy: Policy,
        erasure_policy: Policy,
        identities: Dict[str, Any],
    ) -> Tuple[Dict, Dict]:
        """
        Erasure request with masking_strict set to false,
        meaning we will use deletes to mask data if an update
        is not available
        """

        # store the existing masking_strict value so we can reset it at the end of the test
        masking_strict = CONFIG.execution.masking_strict
        CONFIG.execution.masking_strict = False

        access_results, erasure_results = await self._base_erasure_request(
            access_policy, erasure_policy, identities
        )

        # reset masking_strict value
        CONFIG.execution.masking_strict = masking_strict
        return access_results, erasure_results

    async def _base_erasure_request(
        self,
        access_policy: Policy,
        erasure_policy: Policy,
        identities: Dict[str, Any],
    ) -> Tuple[Dict, Dict]:
        fides_key = self.connection_config.key
        privacy_request = PrivacyRequest(
            id=f"test_{fides_key}_access_request_{random.randint(0, 1000)}"
        )
        identity = Identity(**identities)
        privacy_request.cache_identity(identity)

        # cache external dataset data
        if self.erasure_external_references:
            self.cache.set_encoded_object(
                f"{privacy_request.id}__access_request__{self.connector_type}_external_dataset:{self.connector_type}_external_collection",
                [self.erasure_external_references],
            )

        graph_list = [self.dataset_config.get_graph()]
        connection_config_list = [self.connection_config]
        _process_external_references(self.db, graph_list, connection_config_list)
        dataset_graph = DatasetGraph(*graph_list)

        access_results = await graph_task.run_access_request(
            privacy_request,
            access_policy,
            dataset_graph,
            connection_config_list,
            identities,
            self.db,
        )

        # verify we returned at least one row for each collection in the dataset
        for collection in self.dataset["collections"]:
            assert len(access_results[f"{fides_key}:{collection['name']}"])

        erasure_results = await graph_task.run_erasure(
            privacy_request,
            erasure_policy,
            dataset_graph,
            connection_config_list,
            identities,
            get_cached_data_for_erasures(privacy_request.id),
            self.db,
        )

        return access_results, erasure_results


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


def _external_connection_config(db: Session, fides_key) -> ConnectionConfig:
    connection_config = ConnectionConfig.create(
        db=db,
        data={
            "key": fides_key,
            "name": fides_key,
            "connection_type": ConnectionType.postgres,
            "access": AccessLevel.write,
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

    ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset)

    dataset = DatasetConfig.create(
        db=db,
        data={
            "connection_config_id": connection_config.id,
            "fides_key": fides_key,
            "ctl_dataset_id": ctl_dataset.id,
        },
    )
    return dataset


def _external_dataset(
    connector_type: str, external_references: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate a dataset that contains each external reference as a collection field"""
    # define the email field as an entry point to this dataset
    fields = [
        {
            "name": "email",
            "data_categories": ["user.contact.email"],
            "fidesops_meta": {"data_type": "string", "identity": "email"},
        }
    ]
    # add every external reference as an additional field in this collection
    for external_reference in external_references:
        fields.append(
            {
                "name": external_reference["name"],
                "fidesops_meta": {"data_type": "string"},
            }
        )
    return {
        "fides_key": f"{connector_type}_external_dataset",
        "name": f"{connector_type}_external_dataset",
        "description": f"{connector_type}_external_dataset",
        "collections": [
            {
                "name": f"{connector_type}_external_collection",
                "fields": fields,
            }
        ],
    }


def _process_external_references(
    db: Session,
    graph_list: List[GraphDataset],
    connection_config_list: List[ConnectionConfig],
):
    """
    Read the external references from the base connection config
    and generate the connection config and dataset to represent
    the external references
    """
    # we start with the base connection config
    connection_config = connection_config_list[0]
    if connection_config.saas_config.get("external_references"):
        connector_type = connection_config.saas_config["type"]
        external_connection_config = _external_connection_config(
            db, f"{connector_type}_external_dataset"
        )
        graph_list.append(
            _dataset_config(
                db,
                external_connection_config,
                _external_dataset(
                    connector_type, connection_config.saas_config["external_references"]
                ),
            ).get_graph()
        )
        connection_config_list.append(external_connection_config)


def generate_random_email() -> str:
    return f"{cryptographic_util.generate_secure_random_string(13)}@email.com"
