import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import or_
from sqlalchemy.orm import Session

from fides.api.graph.config import Collection, CollectionAddress
from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_preference import CurrentPrivacyPreference
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.service.connectors.sql_connector import SQLConnector
from fides.api.task.graph_task import build_consent_identity_enrichment_graph
from fides.api.task.task_resources import Connections
from fides.api.util.cache import FidesopsRedis, get_dsr_cache_store
from fides.api.util.collection_util import Row
from fides.config import CONFIG


@dataclass
class _EnrichmentNode:
    """Minimal stand-in for ExecutionNode for identity enrichment queries.

    QueryConfig subclasses access the following attributes:
    - SQLQueryConfig.get_formatted_query_string: node.collection.name (table name)
    - PostgresQueryConfig.generate_table_name: node.collection.name
    - BigQueryQueryConfig: node.collection.name + namespace_meta (set separately)
    - SQLLikeQueryConfig.__init__: node (stored as self.node)
    - QueryConfig.field_map: node.collection.field_dict

    If a future QueryConfig accesses attributes beyond these, this dataclass
    must be extended to match.
    """

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
    connector: SQLConnector,
    dataset_name: str,
    collection: Collection,
    identity_data: Dict[str, Any],
    session: Session,
) -> List[Row]:
    """
    Execute a query against a collection to look up identity fields,
    using the connector's own query_config for correct SQL generation.
    """
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

    logger.info(
        "Identity enrichment: submitting query to {} for {}.{} (timeout={}s)",
        connector.configuration.key,
        dataset_name,
        collection.name,
        CONFIG.consent.identity_enrichment_query_timeout_seconds,
    )
    start = time.monotonic()

    def _run_query() -> List[Row]:
        engine = connector.client()
        with engine.connect() as connection:
            elapsed_connect = time.monotonic() - start
            logger.info(
                "Identity enrichment: connected to {} in {:.2f}s, executing query on {}.{}",
                connector.configuration.key,
                elapsed_connect,
                dataset_name,
                collection.name,
            )
            connector.set_schema(connection)
            results = connection.execute(query)
            return connector.cursor_result_to_rows(results)

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_run_query)
    try:
        rows = future.result(
            timeout=CONFIG.consent.identity_enrichment_query_timeout_seconds
        )
        executor.shutdown(wait=False)
        elapsed_total = time.monotonic() - start
        logger.info(
            "Identity enrichment: query on {}.{} returned {} row(s) in {:.2f}s",
            connector.configuration.key,
            collection.name,
            len(rows),
            elapsed_total,
        )
        return rows
    except FutureTimeoutError:
        executor.shutdown(wait=False, cancel_futures=True)
        elapsed_total = time.monotonic() - start
        logger.error(
            "Identity enrichment query TIMED OUT for {}.{} after {:.2f}s "
            "(limit={}s) - this may indicate the external database is "
            "overloaded or unreachable",
            connector.configuration.key,
            collection.name,
            elapsed_total,
            CONFIG.consent.identity_enrichment_query_timeout_seconds,
        )
        return []
    except Exception as exc:
        executor.shutdown(wait=False)
        elapsed_total = time.monotonic() - start
        logger.warning(
            "Identity enrichment query failed for {}.{} after {:.2f}s: {}",
            connector.configuration.key,
            collection.name,
            elapsed_total,
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


def _enrich_from_current_preferences(
    identity_data: Dict[str, Any],
    session: Session,
) -> Dict[str, Any]:
    """Look up missing email or external_id from CurrentPrivacyPreference.

    Uses indexed hashed identity columns for fast Postgres lookup.
    Returns enriched identity dict, or the original if no match found.
    """
    has_email = bool(identity_data.get("email"))
    has_external_id = bool(identity_data.get("external_id"))

    if has_email and has_external_id:
        return identity_data

    filters = []
    if has_email:
        hashes = CurrentPrivacyPreference.hash_value_for_search(identity_data["email"])
        filters.append(CurrentPrivacyPreference.hashed_email.in_(hashes))
    elif has_external_id:
        hashes = CurrentPrivacyPreference.hash_value_for_search(
            identity_data["external_id"]
        )
        filters.append(CurrentPrivacyPreference.hashed_external_id.in_(hashes))
    else:
        return identity_data

    record = (
        session.query(CurrentPrivacyPreference)
        .filter(or_(*filters))
        .order_by(CurrentPrivacyPreference.updated_at.desc())
        .first()
    )

    if not record:
        return identity_data

    enriched = dict(identity_data)
    if not has_email and record.email:
        enriched["email"] = record.email
    if not has_external_id and record.external_id:
        enriched["external_id"] = record.external_id

    return enriched


def enrich_identities_for_consent(
    datasets: List[DatasetConfig],
    connection_configs: List[ConnectionConfig],
    identity_data: Dict[str, Any],
    privacy_request: PrivacyRequest,
    session: Session,
) -> Dict[str, Any]:
    """
    Resolve additional identities before consent propagation.

    When enabled via FIDES__CONSENT__IDENTITY_ENRICHMENT, first attempts a
    fast lookup from CurrentPrivacyPreference records (indexed Postgres
    query). Falls back to querying consent-enabled DB integrations if the
    local lookup doesn't resolve the missing identity.

    Returns the enriched identity dict. On any failure, returns the original
    identity_data unchanged.
    """
    if not CONFIG.consent.identity_enrichment:
        return identity_data

    if identity_data.get("email") and identity_data.get("external_id"):
        logger.debug(
            "Identity enrichment: both email and external_id already present, skipping"
        )
        return identity_data

    missing = []
    if not identity_data.get("email"):
        missing.append("email")
    if not identity_data.get("external_id"):
        missing.append("external_id")
    logger.info(
        "Identity enrichment: starting, missing identities: {}",
        missing,
    )

    try:
        enriched = _enrich_from_current_preferences(identity_data, session)
        new_keys = set(enriched.keys()) - set(identity_data.keys())
        if new_keys:
            logger.info(
                "Consent identity enrichment (preferences) discovered: {}",
                new_keys,
            )
            _cache_and_log_enrichment(
                enriched,
                new_keys,
                privacy_request,
                session,
                source="preferences",
            )
            return enriched

        enriched = _enrich_from_db_connectors(
            datasets, connection_configs, identity_data, session
        )
        new_keys = set(enriched.keys()) - set(identity_data.keys())
        if new_keys:
            logger.info(
                "Consent identity enrichment (DB connectors) discovered: {}",
                new_keys,
            )
            _cache_and_log_enrichment(
                enriched,
                new_keys,
                privacy_request,
                session,
                source="DB connectors",
            )
            return enriched

        privacy_request.add_success_execution_log(
            session,
            connection_key=None,
            dataset_name="Consent identity enrichment",
            collection_name=None,
            message="No additional identities discovered",
            action_type=ActionType.consent,
        )
        return identity_data

    except Exception as exc:
        logger.warning(
            "Consent identity enrichment failed, proceeding with original identities: {}",
            exc,
        )
        privacy_request.add_error_execution_log(
            session,
            connection_key=None,
            dataset_name="Consent identity enrichment",
            collection_name=None,
            message=f"Consent identity enrichment failed: {exc}",
            action_type=ActionType.consent,
        )
        return identity_data


def _cache_and_log_enrichment(
    enriched: Dict[str, Any],
    new_keys: set,
    privacy_request: PrivacyRequest,
    session: Session,
    source: str,
) -> None:
    """Cache discovered identities in Redis and write an execution log."""
    store = get_dsr_cache_store(privacy_request.id)
    for key in new_keys:
        store.cache_identity_data(
            {key: FidesopsRedis.encode_obj(enriched[key])},
            expire_seconds=CONFIG.redis.default_ttl_seconds,
        )
    privacy_request.add_success_execution_log(
        session,
        connection_key=None,
        dataset_name="Consent identity enrichment",
        collection_name=None,
        message=f"Resolved additional identities via {source}: {', '.join(sorted(new_keys))}",
        action_type=ActionType.consent,
    )


def _enrich_from_db_connectors(
    datasets: List[DatasetConfig],
    connection_configs: List[ConnectionConfig],
    identity_data: Dict[str, Any],
    session: Session,
) -> Dict[str, Any]:
    """Query consent-enabled DB integrations for missing identities."""
    graph = build_consent_identity_enrichment_graph(datasets)
    if not graph.nodes:
        logger.debug("Identity enrichment: no consent-enabled DB connectors in graph")
        return identity_data

    targets = _find_reachable_collections(graph, identity_data)
    if not targets:
        logger.debug(
            "Identity enrichment: graph has %d node(s) but none are "
            "reachable from the seed identities",
            len(graph.nodes),
        )
        return identity_data

    target_descriptions = [f"{conn_key}.{coll.name}" for conn_key, _ds, coll in targets]
    logger.info(
        "Consent identity enrichment: querying %d DB integration(s): %s",
        len(targets),
        target_descriptions,
    )

    start = time.monotonic()
    connections = Connections()
    enriched = dict(identity_data)
    try:
        for connection_key, dataset_name, collection in targets:
            config = _get_connection_config_by_key(connection_configs, connection_key)
            if not config:
                logger.warning(
                    "Identity enrichment: connection config '{}' not found, skipping",
                    connection_key,
                )
                continue

            connector = connections.get_connector(config)
            if not isinstance(connector, SQLConnector):
                logger.debug(
                    "Skipping identity enrichment for non-SQL connector: {}",
                    config.key,
                )
                continue

            rows = _execute_identity_lookup(
                connector, dataset_name, collection, identity_data, session
            )
            discovered = _extract_identities_from_rows(rows, collection, identity_data)
            enriched.update(discovered)
    finally:
        connections.close()

    elapsed = time.monotonic() - start
    logger.info(
        "Consent identity enrichment: DB connector queries completed in {:.2f}s",
        elapsed,
    )
    return enriched
