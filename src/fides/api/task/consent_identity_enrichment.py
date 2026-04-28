from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from fides.api.graph.config import Collection, CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors import get_connector
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.task.graph_task import build_consent_identity_enrichment_graph
from fides.api.util.cache import FidesopsRedis, get_dsr_cache_store
from fides.api.util.collection_util import Row
from fides.config import CONFIG


@dataclass
class _EnrichmentNode:
    """Minimal stand-in for ExecutionNode, providing just what QueryConfig needs."""

    collection: Collection
    address: CollectionAddress
    query_field_paths: set = field(default_factory=set)


def _get_connection_config_by_key(
    connection_configs: List[ConnectionConfig],
    connection_key: str,
) -> Optional[ConnectionConfig]:
    """Find the ConnectionConfig matching the given key."""
    for config in connection_configs:
        if config.key == connection_key:
            return config
    return None


def _find_reachable_collections(
    graph: DatasetGraph,
    identity_data: Dict[str, Any],
) -> List[tuple[str, str, Collection]]:
    """
    Find collections reachable from seed identities.

    Returns (dataset_connection_key, dataset_name, collection) triples
    for any collection that has at least one identity field matching
    a key in identity_data.
    """
    targets: List[tuple[str, str, Collection]] = []
    for node in graph.nodes.values():
        collection = node.collection
        collection_identities = collection.identities()

        has_seed_identity = any(
            id_type in identity_data for id_type in collection_identities.values()
        )
        if has_seed_identity:
            targets.append((node.dataset.connection_key, node.dataset.name, collection))

    return targets


def _execute_identity_lookup(
    connection_config: ConnectionConfig,
    dataset_name: str,
    collection: Collection,
    identity_data: Dict[str, Any],
    session: Session,
) -> List[Row]:
    """
    Execute a query against a collection to look up identity fields,
    using the connector's own query_config for correct SQL generation.
    """
    connector = get_connector(connection_config)
    if not isinstance(connector, SQLConnector):
        logger.debug(
            "Skipping identity enrichment for non-SQL connector: {}",
            connection_config.key,
        )
        return []

    collection_identities = collection.identities()

    filters: Dict[str, List[Any]] = {}
    for field_path, identity_type in collection_identities.items():
        if identity_type in identity_data:
            filters[field_path.string_path] = [identity_data[identity_type]]

    if not filters:
        return []

    select_fields = [fp.string_path for fp in collection_identities.keys()]

    enrichment_node = _EnrichmentNode(
        collection=collection,
        address=CollectionAddress(dataset_name, collection.name),
    )
    namespace_meta = SQLConnector.get_namespace_meta(session, dataset_name)
    query_config = connector.query_config(enrichment_node)  # type: ignore[arg-type]
    if (
        namespace_meta
        and hasattr(query_config, "namespace_meta_schema")
        and query_config.namespace_meta_schema is not None
    ):
        query_config.namespace_meta = query_config.namespace_meta_schema.model_validate(
            namespace_meta
        )

    query = query_config.generate_raw_query(select_fields, filters)
    if query is None:
        return []

    engine = connector.client()
    try:
        with engine.connect() as connection:
            connector.set_schema(connection)
            results = connection.execute(query)
            return SQLConnector.cursor_result_to_rows(results)
    except Exception as exc:
        logger.warning(
            "Identity enrichment query failed for {}.{}: {}",
            connection_config.key,
            collection.name,
            exc,
        )
        return []


def _extract_identities_from_rows(
    rows: List[Row],
    collection: Collection,
    identity_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract identity field values from query results.
    Only returns identities that are missing from identity_data.
    """
    discovered: Dict[str, Any] = {}
    if not rows:
        return discovered

    row = rows[0]
    for field_path, identity_type in collection.identities().items():
        if identity_type in identity_data:
            continue
        value = row.get(field_path.string_path)
        if value is not None:
            discovered[identity_type] = value

    return discovered


def enrich_identities_for_consent(
    datasets: List[DatasetConfig],
    connection_configs: List[ConnectionConfig],
    identity_data: Dict[str, Any],
    privacy_request: PrivacyRequest,
    session: Session,
) -> Dict[str, Any]:
    """
    Resolve additional identities by querying consent-enabled DB integrations
    before consent propagation.

    Always queries reachable collections in consent-enabled DB integrations
    to discover any additional identity fields. This ensures bidirectional
    consent integrations (e.g. Bloomreach needs external_id, Iterable needs
    email) always get the full set of available identities regardless of
    which identity the incoming request provided.

    Returns the enriched identity dict. On any failure, returns the original
    identity_data unchanged.
    """
    try:
        graph = build_consent_identity_enrichment_graph(datasets)
        if not graph.nodes:
            return identity_data

        targets = _find_reachable_collections(graph, identity_data)
        if not targets:
            return identity_data

        logger.info("Consent identity enrichment: querying DB integrations")

        enriched = dict(identity_data)
        for connection_key, dataset_name, collection in targets:
            config = _get_connection_config_by_key(connection_configs, connection_key)
            if not config:
                continue

            rows = _execute_identity_lookup(
                config, dataset_name, collection, identity_data, session
            )
            discovered = _extract_identities_from_rows(rows, collection, identity_data)
            enriched.update(discovered)

        new_keys = set(enriched.keys()) - set(identity_data.keys())
        if new_keys:
            logger.info(
                "Consent identity enrichment discovered: {}",
                new_keys,
            )
            store = get_dsr_cache_store(privacy_request.id)
            for key in new_keys:
                store.cache_identity_data(
                    {key: FidesopsRedis.encode_obj(enriched[key])},
                    expire_seconds=CONFIG.redis.default_ttl_seconds,
                )

        return enriched

    except Exception as exc:
        logger.warning(
            "Consent identity enrichment failed, proceeding with original identities: {}",
            exc,
        )
        return identity_data
